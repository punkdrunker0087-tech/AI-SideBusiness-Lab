extends Node3D

# Toy 0: 磁石は触るだけで楽しいか（仮説H1）
# 検証対象は磁力の曲線そのもの。画面右のスライダーで実行中に変更できる。
# 地形・人数・操作は固定（開発憲章「1ビルド = 1仮説」）。

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
const MIN_DISTANCE := 0.6  # ゼロ距離で力が発散しないための下限

var players: Array = []
var params := {
	"strength": 60.0,  # 磁力の強さ
	"exponent": 2.0,   # 距離減衰の指数（現実の磁石は2〜4。小さいほど遠くまで効く）
	"max_force": 45.0, # 力の上限（近距離での吹っ飛びすぎ防止）
	"range": 5.0,      # 有効距離（これより遠いと磁力ゼロ）。実験ログ#1: 5前後が「いきなり反発、くっつく」で良い
}
var debug_polarity_visible := false
var camera: Camera3D


func _ready() -> void:
	_build_arena()
	_build_light()
	_build_camera()
	_spawn_players()
	_roll_polarities()
	_build_ui()


func _physics_process(_delta: float) -> void:
	_apply_magnet_forces()


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


# --- 磁力 -------------------------------------------------------------------

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
			# 異極（積が-1）なら引き合い、同極（積が+1）なら反発する
			var attract_sign := -float(a.polarity * b.polarity)
			var force: Vector3 = to_b.normalized() * magnitude * attract_sign
			a.magnet_accel += force
			b.magnet_accel -= force


func _roll_polarities() -> void:
	# 全員同極（反発のみ）を避けるため、交互の極性をシャッフルして配る
	var pool: Array[int] = [1, -1, 1, -1]
	pool.shuffle()
	for i in players.size():
		var p = players[i]
		p.polarity = pool[i]
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

		# 開発者用の極性デバッグ表示（Pキー。テストプレイでは絶対に出さない）
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
	# 左右の足場と、それをつなぐ2本の橋（広い橋と細い橋）。下は崖。
	_add_box(Vector3(-12, -0.5, 0), Vector3(12, 1, 12), Color("8d8d86"))  # 左の足場
	_add_box(Vector3(12, -0.5, 0), Vector3(12, 1, 12), Color("8d8d86"))   # 右の足場
	_add_box(Vector3(0, -0.5, -2.5), Vector3(12, 1, 1.8), Color("b8b8ae")) # 広い橋
	_add_box(Vector3(0, -0.5, 2.5), Vector3(12, 1, 0.9), Color("b8b8ae"))  # 細い橋


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


# --- UI（磁力パラメータのスライダー） ---------------------------------------

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	var panel := PanelContainer.new()
	panel.anchor_left = 1.0
	panel.anchor_right = 1.0
	panel.offset_left = -300
	panel.offset_top = 12
	panel.offset_right = -12
	layer.add_child(panel)

	var vbox := VBoxContainer.new()
	panel.add_child(vbox)

	var title := Label.new()
	title.text = "磁力パラメータ（実験用）"
	vbox.add_child(title)

	_add_slider(vbox, "strength", "強さ", 0.0, 200.0, 1.0)
	_add_slider(vbox, "exponent", "減衰指数", 1.0, 4.0, 0.1)
	_add_slider(vbox, "max_force", "力の上限", 5.0, 120.0, 1.0)
	_add_slider(vbox, "range", "有効距離", 2.0, 20.0, 0.5)

	var help := Label.new()
	help.text = "\n1P: WASD+Space / 2P: 矢印+Enter\nゲームパッド: 左スティック+Aボタン\nR: 極性シャッフル\n（Pは開発者専用: 極性デバッグ表示）"
	vbox.add_child(help)


func _add_slider(parent: VBoxContainer, key: String, label_text: String, min_v: float, max_v: float, step: float) -> void:
	var label := Label.new()
	label.text = "%s: %.1f" % [label_text, float(params[key])]
	parent.add_child(label)

	var slider := HSlider.new()
	slider.min_value = min_v
	slider.max_value = max_v
	slider.step = step
	slider.value = params[key]
	slider.custom_minimum_size = Vector2(260, 0)
	slider.value_changed.connect(func(v: float) -> void:
		params[key] = v
		label.text = "%s: %.1f" % [label_text, v]
	)
	parent.add_child(slider)
