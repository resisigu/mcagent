import json, math, os

class CombatAI:
    def __init__(self):
        self.range = 3.0
        self.data_file = os.path.join(os.path.dirname(__file__), "learned_combat.json")
        self.learned = self.load()
        self.previous_health = None
        self.retreat_ticks = 0
        self.jump_attack_ticks = 0
        self.hit_and_run_ticks = 0  # 攻撃直後の緊急離脱用タイマー

    def load(self):
        try:
            with open(self.data_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"attack_distance": 3.0, "bow_distance": 12.0, "samples": 0}

    def step(self, state):
        p = state.get("player") or {}
        mobs = p.get("mobs") or []
        projectiles = state.get("projectiles") or []  # 飛翔体（矢など）のデータ
        
        health = p.get("health")
        if health is not None:
            health = float(health)
            # 被弾時の緊急ノックバック・退避処理
            if self.previous_health is not None and health < self.previous_health - 0.01:
                self.retreat_ticks = max(self.retreat_ticks, 20)
            self.previous_health = health

        if not mobs and not projectiles:
            return self.stop(p)

        yaw = float(p.get("yaw", 0))
        pitch = float(p.get("pitch", 0))
        on_ground = bool(p.get("onGround", False))

        # -------------------------------------------------------------
        # 1. 最優先：矢（飛翔体）の緊急回避ロジック
        # -------------------------------------------------------------
        dodge_move = self.detect_and_dodge_projectiles(projectiles, yaw)
        if dodge_move is not None:
            # 矢が迫っている場合は、旋回・攻撃よりも回避を最優先
            return self.control_for_move(dodge_move, sprint=True, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)

        if not mobs:
            return self.stop(p)

        # ターゲットの選定（最も近い敵）
        target = min(mobs, key=lambda m: float(m.get("distance", 999)))
        x = float(target.get("x", 0))
        y = float(target.get("y", 0))
        z = float(target.get("z", 0))
        horizontal = math.hypot(x, z)

        # 照準計算（Yaw / Pitch）
        desired_yaw = math.degrees(math.atan2(-x, z))
        dyaw = (desired_yaw - yaw + 180) % 360 - 180
        yaw = (yaw + max(-22, min(22, dyaw))) % 360  # 照準速度を少し向上

        desired_pitch = -math.degrees(math.atan2(y + 0.9 - 1.62, max(.001, horizontal)))
        pitch += max(-15, min(15, desired_pitch - pitch))

        aim_ok = abs(((desired_yaw - yaw + 180) % 360) - 180) < 12 and abs(desired_pitch - pitch) < 12
        held = str(p.get("heldItem", "")).lower()
        bow = "bow" in held or "crossbow" in held

        # -------------------------------------------------------------
        # 2. 離れすぎの制御（追撃モード）
        # -------------------------------------------------------------
        # 距離が15m以上離れている場合は、回避計算をスキップして急速接近
        if horizontal > 15.0 and not bow:
            return self.control_for_move((1.0, 0.0), sprint=True, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)

        # 被弾後の緊急退避モード
        if self.retreat_ticks > 0:
            self.retreat_ticks -= 1
            return self.control_for_move(self.best_escape(mobs, prefer_back=True), sprint=True, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)

        # -------------------------------------------------------------
        # 3. 弓装備時の動き
        # -------------------------------------------------------------
        if bow:
            ideal = float(self.learned.get("bow_distance", 12.0))
            if horizontal < 6.0:  # 接近されすぎたら距離をとる
                return self.control_for_move(self.best_escape(mobs, prefer_back=True), sprint=True, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)
            attack = aim_ok and horizontal <= ideal + 2.0
            forward = 1.0 if horizontal > ideal + 1.0 else (-0.5 if horizontal < ideal - 1.5 else 0)
            return self.control_for_move((forward, self.strafe(x, z)), sprint=False, attack=attack, yaw=yaw, pitch=pitch, on_ground=False, use=attack)

        # -------------------------------------------------------------
        # 4. 近接戦闘：被ダメージ最小化（ヒット＆アウェイ ＆ サークリング）
        # -------------------------------------------------------------
        ideal_dist = max(2.8, min(3.1, float(self.learned.get("attack_distance", 3.0))))
        nearby_count = sum(1 for m in mobs if float(m.get("distance", 999)) <= 3.5)

        # 攻撃をヒットさせた直後：相手の反撃範囲から瞬時にバックステップ
        if self.hit_and_run_ticks > 0:
            self.hit_and_run_ticks -= 1
            return self.control_for_move((-1.0, self.strafe(x, z)), sprint=False, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)

        # 敵が複数いる場合：囲まれないように円運動をしつつ間合いを維持
        if nearby_count >= 2:
            move = self.best_escape(mobs, prefer_back=False)
            attack = aim_ok and 2.5 <= horizontal <= 3.15 and self.attack_ready(p)
            return self.control_for_move(move, sprint=False, attack=attack, yaw=yaw, pitch=pitch, on_ground=on_ground, target_id=target.get("id"))

        # 敵の攻撃間合い（2.35m未満）に踏み込まれた場合
        if horizontal < 2.35:
            # 敵の脅威度が高い場合は横に大きく回り込んで視界から外れる
            if self.enemy_threatens(target):
                circle_move = (-0.5, 1.0 if x > 0 else -1.0)
                return self.control_for_move(circle_move, sprint=True, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)
            
            # クールダウンが上がっていれば攻撃して即離脱準備
            if aim_ok and self.attack_ready(p):
                self.hit_and_run_ticks = 4  # 4ティックス（約0.2秒）間バックステップ
                return self.control_for_move((0.0, self.strafe(x, z)), sprint=False, attack=True, yaw=yaw, pitch=pitch, on_ground=on_ground, target_id=target.get("id"))
            
            return self.control_for_move((-0.8, self.strafe(x, z)), sprint=False, attack=False, yaw=yaw, pitch=pitch, on_ground=on_ground)

        # 理想の間合い（クリティカルジャンプ攻撃の判定）
        if horizontal <= ideal_dist + 0.2 and aim_ok:
            if on_ground and self.jump_attack_ticks <= 0 and self.attack_ready(p):
                self.jump_attack_ticks = 10
                return self.control_for_move((0.3, self.strafe(x, z)), sprint=False, attack=False, yaw=yaw, pitch=pitch, on_ground=True)
            
            if self.jump_attack_ticks > 0:
                self.jump_attack_ticks -= 1
                # 落下中に攻撃（クリティカルヒット）
                if float(p.get("fallDistance", 0)) > 0.02:
                    self.jump_attack_ticks = 0
                    self.hit_and_run_ticks = 3  # 攻撃ヒット後離脱
                    return self.control_for_move((0.0, self.strafe(x, z)), sprint=False, attack=self.attack_ready(p), yaw=yaw, pitch=pitch, on_ground=False, target_id=target.get("id"))
                return self.control_for_move((0.0, self.strafe(x, z)), sprint=False, attack=False, yaw=yaw, pitch=pitch, on_ground=False)

        # 間合いを詰める（間合いの維持）
        if horizontal > ideal_dist + 0.3:
            return self.control_for_move((1.0, self.strafe(x, z)), sprint=True, attack=False, yaw=yaw, pitch=pitch, on_ground=False)

        # 通常の牽制・攻撃
        can_attack = self.attack_ready(p) and aim_ok
        if can_attack:
            self.hit_and_run_ticks = 3
        return self.control_for_move((0.0, self.strafe(x, z)), sprint=False, attack=can_attack, yaw=yaw, pitch=pitch, on_ground=on_ground, target_id=target.get("id"))

    # -------------------------------------------------------------
    # 補助機能：矢の検知と回避移動ベクトルの計算
    # -------------------------------------------------------------
    def detect_and_dodge_projectiles(self, projectiles, current_yaw):
        """迫り来る矢を検知し、垂直方向へ回避する移動ベクトル (forward, strafe) を返す"""
        for proj in projectiles:
            # 矢の相対座標と速度ベクトル
            px, py, pz = float(proj.get("x", 0)), float(proj.get("y", 0)), float(proj.get("z", 0))
            vx, vy, vz = float(proj.get("vx", 0)), float(proj.get("vy", 0)), float(proj.get("vz", 0))
            
            dist = math.hypot(px, pz)
            speed = math.hypot(vx, vz)

            if dist > 20.0 or speed < 0.2:
                continue

            # 矢がプレイヤーに向かっているか判断（内積判定）
            # px, pz はプレイヤーから見た矢の位置なので、(-px, -pz) がプレイヤーへの方向
            dot_product = (vx * -px) + (vz * -pz)
            if dot_product > 0:  # プレイヤーに向かって近づいている
                # 衝突予測時間の計算 (t seconds)
                t = (px * vx + pz * vz) / (speed ** 2)
                if 0 < -t < 1.5:  # 1.5秒以内に到達予定
                    # 矢の移動方向に対して垂直に回避ステップを踏む
                    # プレイヤーの向き（Yaw）に合わせて相対的な strafe 方向を決定
                    proj_angle = math.atan2(vz, vx)
                    rad_yaw = math.radians(current_yaw)
                    
                    # 左右どちらかへ即座に緊急回避（strafe: 1.0 または -1.0）
                    dodge_strafe = 1.0 if math.sin(proj_angle - rad_yaw) > 0 else -1.0
                    return (0.0, dodge_strafe)
        return None

    def attack_ready(self, p):
        return float(p.get("attackStrength", 1.0)) >= 0.92

    def enemy_threatens(self, m):
        d = float(m.get("distance", 999))
        vx, vz = float(m.get("vx", 0)), float(m.get("vz", 0))
        x, z = float(m.get("x", 0)), float(m.get("z", 0))
        speed = math.hypot(vx, vz)
        closing = x * vx + z * vz
        return d <= 3.5 and (int(m.get("hurtTime", 0)) > 0 or (speed > 0.08 and closing < -(speed * d * 0.35)))

    def best_escape(self, mobs, prefer_back=False):
        best = (0, 0)
        best_score = -1e9
        bx = bz = 0
        for m in mobs:
            x, z = float(m.get("x", 0)), float(m.get("z", 0))
            d = max(.35, math.hypot(x, z))
            bx -= x / (d * d)
            bz -= z / (d * d)
        bl = math.hypot(bx, bz)
        if bl:
            bx /= bl
            bz /= bl

        for i in range(24):
            a = 2 * math.pi * i / 24
            dx, dz = math.sin(a), math.cos(a)
            score = 2.5 * (dx * bx + dz * bz) if prefer_back else 0
            min_d = 999
            for m in mobs:
                x, z = float(m.get("x", 0)), float(m.get("z", 0))
                d = math.hypot(x, z)
                min_d = min(min_d, d)
                if d < .01:
                    continue
                score += 2 * ((dx * (-x / d) + dz * (-z / d)) / max(1, d))
                if x * dx + z * dz < 0:
                    score += .7
                if d < 3:
                    score += 2.2 * (1 - d / 3)
            score += min_d * .4
            if score > best_score:
                best_score = score
                best = (dx, dz)
        return best

    def control_for_move(self, move, sprint, attack, yaw, pitch, on_ground, target_id=None, use=False):
        dx, dz = move
        l = math.hypot(dx, dz)
        if l > .001:
            dx /= l
            dz /= l
        r = math.radians(yaw)
        forward = dz * math.cos(r) - dx * math.sin(r)
        strafe = dx * math.cos(r) + dz * math.sin(r)
        return {
            "forward": max(-1, min(1, forward)),
            "strafe": max(-1, min(1, strafe)),
            "jump": bool(on_ground and sprint),
            "sprint": sprint,
            "attack": attack,
            "use": use,
            "yaw": yaw,
            "pitch": pitch,
            "targetId": target_id
        }

    def stop(self, p):
        return {"forward": 0, "strafe": 0, "jump": False, "sprint": False, "attack": False, "use": False, "yaw": p.get("yaw", 0), "pitch": p.get("pitch", 0)}

    def strafe(self, x, z):
        if abs(x) < .2:
            return 0
        return -.55 if x > 0 else .55
