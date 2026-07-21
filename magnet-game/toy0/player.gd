extends CharacterBody3D

# プレイヤー1人ぶんの移動・ジャンプ・磁力の受け取り・復帰。
# 極性(polarity)はここに保持するが、UIには絶対に出さない（開発憲章）。
# Pキーのデバッグ表示だけが例外（開発者用）。

const SPEED := 6.0
const JUMP := 8.5
const GRAVITY := 22.0
const EXTERNAL_DAMPING := 3.0
const KILL_Y := -10.0

var device := 0                 # 0〜3 = ゲームパッド番号
var use_keyboard_wasd := false  # 1PはWASD+Spaceでも操作できる
var use_keyboard_arrows := false# 2Pは矢印キー+Enterでも操作できる（一人でも両手で試せるように）
var polarity := 1               # +1 / -1
var spawn_point := Vector3.ZERO
var magnet_accel := Vector3.ZERO # game.gd が毎フレーム書き込む

var external := Vector3.ZERO    # 磁力・吹っ飛びによる速度（操作と分離して減衰させる）


func _physics_process(delta: float) -> void:
	var move := _read_move()

	external += Vector3(magnet_accel.x, 0.0, magnet_accel.z) * delta
	external = external.lerp(Vector3.ZERO, minf(1.0, EXTERNAL_DAMPING * delta))

	velocity.x = move.x * SPEED + external.x
	velocity.z = move.y * SPEED + external.z
	velocity.y -= GRAVITY * delta
	velocity.y += magnet_accel.y * delta

	if _jump_held() and is_on_floor():
		velocity.y = JUMP

	move_and_slide()

	if global_position.y < KILL_Y:
		respawn()


func respawn() -> void:
	global_position = spawn_point
	velocity = Vector3.ZERO
	external = Vector3.ZERO


func _read_move() -> Vector2:
	var v := Vector2.ZERO
	v.x = Input.get_joy_axis(device, JOY_AXIS_LEFT_X)
	v.y = Input.get_joy_axis(device, JOY_AXIS_LEFT_Y)
	if v.length() < 0.15:  # スティックのドリフト対策
		v = Vector2.ZERO
	if use_keyboard_wasd:
		if Input.is_key_pressed(KEY_A):
			v.x -= 1.0
		if Input.is_key_pressed(KEY_D):
			v.x += 1.0
		if Input.is_key_pressed(KEY_W):
			v.y -= 1.0
		if Input.is_key_pressed(KEY_S):
			v.y += 1.0
	if use_keyboard_arrows:
		if Input.is_key_pressed(KEY_LEFT):
			v.x -= 1.0
		if Input.is_key_pressed(KEY_RIGHT):
			v.x += 1.0
		if Input.is_key_pressed(KEY_UP):
			v.y -= 1.0
		if Input.is_key_pressed(KEY_DOWN):
			v.y += 1.0
	return v.limit_length(1.0)


func _jump_held() -> bool:
	if Input.is_joy_button_pressed(device, JOY_BUTTON_A):
		return true
	if use_keyboard_wasd and Input.is_key_pressed(KEY_SPACE):
		return true
	if use_keyboard_arrows and Input.is_key_pressed(KEY_ENTER):
		return true
	return false
