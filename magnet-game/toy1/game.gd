extends Node3D

# Toy 1: 事故は笑いになるか（仮説H2・H4）
# ベースはToy 0と同じ磁力（値は実験ログ#1〜#3で確定したレシピを継承）。
# 追加要素は「変換ボタン」（テストA/B/Cを1/2/3キーで切り替え）と「重い鉄球」のみ。
# Toy 0.5（目的テキスト）はH6用の別仮説なのでここには持ち込まない（原則1・3）。

const PLAYER_SCRIPT := preload("res://player.gd")
const PLAYER_COLORS: Array[Color] = [
	Color("e5484d"),  # 1P 赤（※色は個人の識別。極性とは無関係にする）
	Color("3f8cff"),  # 2P 青
	Color("46a758"),  # 3P 緑
	Color("ffb224"),  # 4P 黄
]
const SPAWNS: Array[Vector3] = [
	Vector3(-12, 2, -2.5),
	Vector3(-12, 2, 2.5),
	Vector3(12, 2, -2.5),
	Vector3(12, 2, 2.5),
]
const MIN_DISTANCE := 0.6

const BUTTON_POSITION := Vector3(-9, 0.6, 0)
const BUTTON_RADIUS := 1.5
const HAMMER_IMPULSE := 9.0
const HAMMER_UP := 4.0

const IRON_SPAWN := Vector3(0, 2, -2.5)
const IRON_MASS := 4.0
const IRON_STRENGTH := 320.0
const IRON_EXPONENT := 1.5
const IRON_MAX_FORCE := 650.0
const IRON_RANGE := 6.0
const KILL_Y := -10.0

var players: Array = []
var params := {
	# 実験ログ#1〜#3で確定したレシピをそのまま継承（Toy 1の検証対象はここではない）
	"strength": 30.0,
	"exponent": 1.5,
	"max_force": 45.0,
	"range": 5.0,
}
var debug_polarity_visible := false
var camera: Camera3D
var iron_ball: RigidBody3D
var button_mesh: MeshInstance3D
var test_mode := "A"  # A: 反転あり・事故あり / B: 反転なし・事故あり(ハンマー) / C: 反転あり・事故なし
var mode_label: Label


func _ready() -> void:
	_build_arena()
	_build_light()
	_build_camera()
	_spawn_players()
	_roll_polarities()
	_build_iron_ball()
	_build_button()
	_build_ui()


func _physics_process(_delta: float) -> void:
	_apply_magnet_forces()
	_apply_iron_pull()
	_check_button_interactions()
	if iron_ball.global_position.y < KILL_Y:
		iron_ball.global_position = IRON_SPAWN
		iron_ball.linear_velocity = Vector3.ZERO
		iron_ball.angular_velocity = Vector3.ZERO


func _process(delta: float) -> void:
	_update_camera(delta)


func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_R:
				_roll_polarities()
			KEY_P:
				debug_polarity_visible = not debug_polarity_visible
				for p in players:
					p.get_node("PolarityDebug").visible = debug_polarity_visible
			KEY_1:
				_set_test_mode("A")
			KEY_2:
				_set_test_mode("B")
			KEY_3:
				_set_test_mode("C")


func _set_test_mode(mode: String) -> void:
	test_mode = mode
	var names := {"A": "A（変換・反転あり事故あり）", "B": "B（ハンマー・反転なし事故あり）", "C": "C（全員反転・事故なし）"}
	mode_label.text = "テストモード: %s" % names[mode]


# --- ボタン ------------------------------------------------------------------

func _check_button_interactions() -> void:
	for p in players:
		var pressed: bool = p.interact_just_pressed()
		if not pressed:
			continue
		if p.global_position.distance_to(BUTTON_POSITION) > BUTTON_RADIUS:
			continue
		_trigger_button(p)


func _trigger_button(presser) -> void:
	match test_mode:
		"A":
			presser.polarity *= -1
			_update_polarity_marker(presser)
		"B":
			var target = _nearest_other_player(presser)
			if target == null:
				return
			var dir: Vector3 = target.global_position - presser.global_position
			if dir.length() < 0.01:
				dir = Vector3.FORWARD
			target.external += dir.normalized() * HAMMER_IMPULSE + Vector3(0, HAMMER_UP, 0)
		"C":
			for p in players:
				p.polarity *= -1
				_update_polarity_marker(p)


func _nearest_other_player(from):
	var best = null
	var best_dist := INF
	for p in players:
		if p == from:
			continue
		var d: float = from.global_position.distance_to(p.global_position)
		if d < best_dist:
			best_dist = d
			best = p
	return best


func _build_button() -> void:
	var body := StaticBody3D.new()
	body.position = BUTTON_POSITION

	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.8, 0.4, 0.8)
	shape.shape = box
	body.add_child(shape)

	button_mesh = MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.4
	mesh.bottom_radius = 0.4
	mesh.height = 0.4
	button_mesh.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("ffd93d")
	mat.emission_enabled = true
	mat.emission = Color("ffd93d")
	mat.emission_energy_multiplier = 0.6
	button_mesh.set_surface_override_material(0, mat)
	body.add_child(button_mesh)

	add_child(body)


# --- 鉄球（一人では動かない） -----------------------------------------------

func _build_iron_ball() -> void:
	iron_ball = RigidBody3D.new()
	iron_ball.global_position = IRON_SPAWN
	iron_ball.mass = IRON_MASS
	iron_ball.linear_damp = 2.5
	iron_ball.angular_damp = 2.0

	var shape := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 0.6
	shape.shape = sphere
	iron_ball.add_child(shape)

	var mesh := MeshInstance3D.new()
	var sphere_mesh := SphereMesh.new()
	sphere_mesh.radius = 0.6
	sphere_mesh.height = 1.2
	mesh.mesh = sphere_mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("4a4a52")
	mat.metallic = 0.7
	mat.roughness = 0.3
	mesh.set_surface_override_material(0, mat)
	iron_ball.add_child(mesh)

	add_child(iron_ball)


func _apply_iron_pull() -> void:
	for p in players:
		var to_ball: Vector3 = iron_ball.global_position - p.global_position
		var d := maxf(to_ball.length(), MIN_DISTANCE)
		if d > IRON_RANGE:
			continue
		# 鉄は極性を持たない: 誰であっても常に引き寄せる（開発憲章の物理設定）
		var magnitude: float = minf(IRON_STRENGTH / pow(d, IRON_EXPONENT), IRON_MAX_FORCE)
		iron_ball.apply_central_force(to_ball.normalized() * magnitude)


# --- 磁力（プレイヤー間・Toy 0から継承） -------------------------------------

func _apply_magnet_forces() -> void:
	for p in players:
		p.magnet_accel = Vector3.ZERO
	for i in players.size():
		for j in range(i + 1, players.size()):
			var a = players[i]
			var b = players[j]
			var to_b: Vector3 = b.global_position - a.global_position
			var d := maxf(to_b.length(), MIN_DISTANCE)
			if d > params.range:
				continue
			var magnitude: float = minf(
				params.strength / pow(d, params.exponent),
				params.max_force
			)
			var attract_sign := -float(a.polarity * b.polarity)
			var force: Vector3 = to_b.normalized() * magnitude * attract_sign
			a.magnet_accel += force
			b.magnet_accel -= force


func _roll_polarities() -> void:
	var pool: Array[int] = [1, -1, 1, -1]
	pool.shuffle()
	for i in players.size():
		players[i].polarity = pool[i]
		_update_polarity_marker(players[i])


func _update_polarity_marker(p) -> void:
	var marker: MeshInstance3D = p.get_node("PolarityDebug")
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color.RED if p.polarity > 0 else Color.BLUE
	marker.set_surface_override_material(0, mat)


# --- 生成 -------------------------------------------------------------------

func _spawn_players() -> void:
	for i in 4:
		var p := CharacterBody3D.new()
		p.name = "Player%d" % (i + 1)
		p.set_script(PLAYER_SCRIPT)

		var shape := CollisionShape3D.new()
		var capsule := CapsuleShape3D.new()
		capsule.radius = 0.45
		capsule.height = 1.6
		shape.shape = capsule
		p.add_child(shape)

		var mesh := MeshInstance3D.new()
		var capsule_mesh := CapsuleMesh.new()
		capsule_mesh.radius = 0.45
		capsule_mesh.height = 1.6
		mesh.mesh = capsule_mesh
		var mat := StandardMaterial3D.new()
		mat.albedo_color = PLAYER_COLORS[i]
		mesh.set_surface_override_material(0, mat)
		p.add_child(mesh)

		var marker := MeshInstance3D.new()
		marker.name = "PolarityDebug"
		var sphere := SphereMesh.new()
		sphere.radius = 0.18
		sphere.height = 0.36
		marker.mesh = sphere
		marker.position = Vector3(0, 1.3, 0)
		marker.visible = false
		p.add_child(marker)

		add_child(p)
		p.device = i
		p.use_keyboard_wasd = (i == 0)
		p.use_keyboard_arrows = (i == 1)
		p.spawn_point = SPAWNS[i]
		p.global_position = SPAWNS[i]
		players.append(p)


func _build_arena() -> void:
	_add_box(Vector3(-12, -0.5, 0), Vector3(12, 1, 12), Color("8d8d86"))
	_add_box(Vector3(12, -0.5, 0), Vector3(12, 1, 12), Color("8d8d86"))
	_add_box(Vector3(0, -0.5, -2.5), Vector3(12, 1, 1.8), Color("b8b8ae"))
	_add_box(Vector3(0, -0.5, 2.5), Vector3(12, 1, 0.9), Color("b8b8ae"))


func _add_box(center: Vector3, size: Vector3, color: Color) -> void:
	var body := StaticBody3D.new()
	body.position = center

	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)

	var mesh := MeshInstance3D.new()
	var box_mesh := BoxMesh.new()
	box_mesh.size = size
	mesh.mesh = box_mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mesh.set_surface_override_material(0, mat)
	body.add_child(mesh)

	add_child(body)


func _build_light() -> void:
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-55, -30, 0)
	light.shadow_enabled = true
	add_child(light)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("1c1c22")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.6, 0.6, 0.65)
	e.ambient_light_energy = 0.7
	env.environment = e
	add_child(env)


func _build_camera() -> void:
	camera = Camera3D.new()
	camera.position = Vector3(0, 20, 24)
	camera.rotation_degrees = Vector3(-42, 0, 0)
	add_child(camera)
	camera.make_current()


func _update_camera(delta: float) -> void:
	if players.is_empty():
		return
	var center := Vector3.ZERO
	for p in players:
		center += p.global_position
	center /= players.size()
	var target := Vector3(center.x * 0.4, 20, 24)
	camera.position = camera.position.lerp(target, minf(1.0, 3.0 * delta))


# --- UI ----------------------------------------------------------------------

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	var panel := PanelContainer.new()
	panel.anchor_left = 1.0
	panel.anchor_right = 1.0
	panel.offset_left = -320
	panel.offset_top = 12
	panel.offset_right = -12
	layer.add_child(panel)

	var vbox := VBoxContainer.new()
	panel.add_child(vbox)

	mode_label = Label.new()
	add_theme_font_size(mode_label, 20)
	vbox.add_child(mode_label)
	_set_test_mode(test_mode)

	var help := Label.new()
	help.text = (
		"\n1P: WASD+Space+E / 2P: 矢印+Enter+/\n"
		+ "ゲームパッド: 左スティック+A(ジャンプ)+X(操作)\n"
		+ "黄色いボタンに近づいてE/X/で作動\n\n"
		+ "1/2/3: テストモード切替（開発者用）\n"
		+ "R: 極性シャッフル / P: 極性デバッグ表示"
	)
	vbox.add_child(help)


func add_theme_font_size(label: Label, size: int) -> void:
	label.add_theme_font_size_override("font_size", size)
