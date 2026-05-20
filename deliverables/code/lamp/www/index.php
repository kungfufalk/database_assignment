<?php
declare(strict_types=1);

date_default_timezone_set('Europe/Athens');

function env_or_default(string $name, string $default): string
{
	$value = getenv($name);
	return $value === false || $value === '' ? $default : $value;
}

function pdo(): ?PDO
{
	static $pdo = null;
	if ($pdo instanceof PDO) {
		return $pdo;
	}

	$host = env_or_default('DB_HOST', 'mariadb');
	$port = env_or_default('DB_PORT', '3306');
	$dbName = env_or_default('DB_NAME', 'ygeiopolis');
	$user = env_or_default('DB_USER', 'root');
	$password = env_or_default('DB_PASSWORD', 'your_password');

	try {
		$pdo = new PDO(
			"mysql:host={$host};port={$port};dbname={$dbName};charset=utf8mb4",
			$user,
			$password,
			[
				PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
				PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
				PDO::ATTR_EMULATE_PREPARES => false,
			]
		);
	} catch (Throwable $exception) {
		$pdo = null;
		$GLOBALS['db_error'] = $exception->getMessage();
	}

	return $pdo;
}

function h(mixed $value): string
{
	return htmlspecialchars((string) $value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function request_method(): string
{
	return strtoupper($_SERVER['REQUEST_METHOD'] ?? 'GET');
}

function param(string $key, mixed $default = null): mixed
{
	return $_GET[$key] ?? $_POST[$key] ?? $default;
}

function redirect_to(array $params = []): never
{
	$base = strtok($_SERVER['REQUEST_URI'] ?? '/', '?') ?: '/';
	$query = $params ? '?' . http_build_query($params) : '';
	header('Location: ' . $base . $query);
	exit;
}

function flash_set(string $type, string $message): void
{
	if (session_status() !== PHP_SESSION_ACTIVE) {
		session_start();
	}

	$_SESSION['flash'] = ['type' => $type, 'message' => $message];
}

function flash_get(): ?array
{
	if (session_status() !== PHP_SESSION_ACTIVE) {
		session_start();
	}

	if (!isset($_SESSION['flash'])) {
		return null;
	}

	$flash = $_SESSION['flash'];
	unset($_SESSION['flash']);
	return $flash;
}

function fetch_one(string $sql, array $params = []): ?array
{
	$pdo = pdo();
	if (!$pdo instanceof PDO) {
		return null;
	}

	$statement = $pdo->prepare($sql);
	$statement->execute($params);
	$row = $statement->fetch();
	return $row === false ? null : $row;
}

function fetch_all(string $sql, array $params = []): array
{
	$pdo = pdo();
	if (!$pdo instanceof PDO) {
		return [];
	}

	$statement = $pdo->prepare($sql);
	$statement->execute($params);
	return $statement->fetchAll();
}

function count_rows(string $sql, array $params = []): int
{
	$row = fetch_one($sql, $params);
	if ($row === null) {
		return 0;
	}

	$value = array_values($row)[0] ?? 0;
	return (int) $value;
}

function execute_sql(string $sql, array $params = []): int
{
	$pdo = pdo();
	if (!$pdo instanceof PDO) {
		throw new RuntimeException('Database connection is not available.');
	}

	$statement = $pdo->prepare($sql);
	$statement->execute($params);
	return $statement->rowCount();
}

function safe_limit_value(mixed $value, int $default = 25, int $max = 100): int
{
	$limit = filter_var($value, FILTER_VALIDATE_INT);
	if ($limit === false || $limit <= 0) {
		return $default;
	}

	return min($limit, $max);
}

function selected(string $value, mixed $current): string
{
	return (string) $current === $value ? 'selected' : '';
}

function app_title(string $page): string
{
	return match ($page) {
		'patients' => 'Patients',
		'patient' => 'Patient details',
		'patient-edit' => 'Edit patient',
		'patient-new' => 'New patient',
		'departments' => 'Departments',
		'department' => 'Department details',
		'department-edit' => 'Edit department',
		'department-new' => 'New department',
		'hospitalizations' => 'Hospitalizations',
		'hospitalization' => 'Hospitalization details',
		'drugs' => 'Drugs',
		'drug' => 'Drug details',
		'staff' => 'Staff',
		'search' => 'Search',
		default => 'Ygeiopolis Hospital Database',
	};
}

function render_header(string $page): void
{
	$title = app_title($page);
	$flash = flash_get();
	$dbOk = pdo() instanceof PDO;
	$nav = [
		'dashboard' => 'Dashboard',
		'patients' => 'Patients',
		'departments' => 'Departments',
		'hospitalizations' => 'Hospitalizations',
		'staff' => 'Staff',
		'drugs' => 'Drugs',
		'search' => 'Search',
	];
	?>
<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title><?= h($title) ?></title>
	<style>
		:root {
			--bg: #0b1220;
			--panel: #111a2e;
			--text: #e5eefc;
			--muted: #93a4c3;
			--accent: #8bd1ff;
			--accent-2: #69f0ae;
			--danger: #ff7a90;
			--border: rgba(255,255,255,.08);
			--shadow: 0 24px 60px rgba(0,0,0,.35);
		}
		* { box-sizing: border-box; }
		body {
			margin: 0;
			font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
			background:
				radial-gradient(circle at top left, rgba(139,209,255,.18), transparent 28%),
				radial-gradient(circle at top right, rgba(105,240,174,.12), transparent 25%),
				linear-gradient(180deg, #060a12 0%, var(--bg) 100%);
			color: var(--text);
		}
		a { color: var(--accent); text-decoration: none; }
		a:hover { text-decoration: underline; }
		.shell { max-width: 1440px; margin: 0 auto; padding: 24px; }
		.topbar {
			display: flex; align-items: center; justify-content: space-between; gap: 16px;
			padding: 18px 20px; border: 1px solid var(--border); border-radius: 22px;
			background: rgba(13, 20, 37, .86); backdrop-filter: blur(14px); box-shadow: var(--shadow);
			margin-bottom: 24px;
		}
		.brand { display: flex; flex-direction: column; gap: 4px; }
		.brand strong { font-size: 1.05rem; letter-spacing: .02em; }
		.brand span { color: var(--muted); font-size: .9rem; }
		.nav { display: flex; flex-wrap: wrap; gap: 10px; }
		.nav a {
			padding: 10px 14px; border-radius: 999px; border: 1px solid var(--border);
			background: rgba(255,255,255,.03); color: var(--text);
		}
		.nav a.active { background: rgba(139,209,255,.18); border-color: rgba(139,209,255,.35); }
		.grid { display: grid; gap: 20px; }
		.grid.cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
		.grid.cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
		.grid.cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
		.card, .panel {
			background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
			border: 1px solid var(--border); border-radius: 22px; box-shadow: var(--shadow);
		}
		.card { padding: 18px; }
		.panel { padding: 20px; }
		.kpi { display: flex; flex-direction: column; gap: 6px; }
		.kpi span { color: var(--muted); font-size: .88rem; }
		.kpi strong { font-size: 2rem; line-height: 1; }
		.section-head { display: flex; align-items: end; justify-content: space-between; gap: 16px; margin: 0 0 14px; }
		h1, h2, h3 { margin: 0; }
		h1 { font-size: 2rem; }
		h2 { font-size: 1.3rem; }
		p { color: var(--muted); }
		table { width: 100%; border-collapse: collapse; }
		th, td { text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
		th { color: #cfe2ff; font-size: .9rem; white-space: nowrap; }
		td { color: #eff5ff; }
		tr:hover td { background: rgba(255,255,255,.02); }
		.muted { color: var(--muted); }
		.badge {
			display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 999px;
			border: 1px solid var(--border); background: rgba(255,255,255,.04); font-size: .82rem;
		}
		.badge.ok { border-color: rgba(105,240,174,.3); background: rgba(105,240,174,.12); }
		.badge.warn { border-color: rgba(255,122,144,.3); background: rgba(255,122,144,.12); }
		.actions { display: flex; flex-wrap: wrap; gap: 10px; }
		.button, button, input[type="submit"] {
			appearance: none; border: 1px solid rgba(139,209,255,.35); background: rgba(139,209,255,.15);
			color: var(--text); padding: 10px 14px; border-radius: 12px; font: inherit; cursor: pointer;
		}
		.button.secondary { border-color: var(--border); background: rgba(255,255,255,.04); }
		.button.danger, .danger button, button.danger {
			border-color: rgba(255,122,144,.4); background: rgba(255,122,144,.16);
		}
		input, select, textarea {
			width: 100%; padding: 11px 12px; border-radius: 12px; border: 1px solid var(--border);
			background: rgba(7,12,24,.88); color: var(--text); font: inherit;
		}
		textarea { min-height: 110px; resize: vertical; }
		label { display: block; margin-bottom: 8px; color: #d8e6ff; font-size: .92rem; }
		.form-grid { display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
		.form-grid .full { grid-column: 1 / -1; }
		.flash { margin: 0 0 18px; padding: 14px 16px; border-radius: 14px; border: 1px solid var(--border); }
		.flash.success { background: rgba(105,240,174,.14); border-color: rgba(105,240,174,.35); }
		.flash.error { background: rgba(255,122,144,.14); border-color: rgba(255,122,144,.35); }
		.grid-list { display: grid; gap: 18px; }
		.split { display: grid; gap: 20px; grid-template-columns: 1.3fr .7fr; }
		.stack { display: grid; gap: 12px; }
		.small { font-size: .9rem; }
		.overflow { overflow-x: auto; }
		tr.row-selectable { cursor: pointer; }
		tr.row-selectable:hover td { background: rgba(139,209,255,.08); }
		tr.row-selected td { background: rgba(105,240,174,.10); }
		@media (max-width: 1100px) {
			.grid.cols-2, .grid.cols-3, .grid.cols-4, .split, .form-grid { grid-template-columns: 1fr; }
		}
	</style>
	<script>
		document.addEventListener('click', function (event) {
			const row = event.target.closest('tr[data-row-select]');
			if (!row) {
				return;
			}

			if (event.target.closest('a, button, input, select, textarea, label, form')) {
				return;
			}

			const href = row.getAttribute('data-href');
			if (href) {
				window.location.href = href;
				return;
			}

			row.classList.toggle('row-selected');
		});

		document.addEventListener('keydown', function (event) {
			const row = event.target.closest('tr[data-row-select]');
			if (!row) {
				return;
			}

			if (event.key === 'Enter' || event.key === ' ') {
				event.preventDefault();
				const href = row.getAttribute('data-href');
				if (href) {
					window.location.href = href;
					return;
				}
				row.classList.toggle('row-selected');
			}
		});
	</script>
</head>
<body>
<div class="shell">
	<header class="topbar">
		<div class="brand">
			<strong>Ygeiopolis General Hospital</strong>
			<span>SQL web UI</span>
		</div>
		<nav class="nav" aria-label="Primary">
			<?php foreach ($nav as $route => $label): ?>
				<a class="<?= $page === $route ? 'active' : '' ?>" href="?page=<?= h($route) ?>"><?= h($label) ?></a>
			<?php endforeach; ?>
		</nav>
	</header>
	<?php if ($flash !== null): ?>
		<div class="flash <?= h($flash['type']) ?>"><?= h($flash['message']) ?></div>
	<?php endif; ?>
	<?php if (!$dbOk): ?>
		<div class="flash error">
			Database connection failed. <?= h($GLOBALS['db_error'] ?? 'Unknown error') ?>
		</div>
	<?php endif; ?>
	<?php
}

function render_footer(): void
{
	?>
</div>
</body>
</html>
	<?php
}

function dashboard_page(): void
{
	$counts = [
		'Patients' => count_rows('SELECT COUNT(*) AS total FROM patient'),
		'Hospitalizations' => count_rows('SELECT COUNT(*) AS total FROM hospitalization'),
		'Doctors' => count_rows('SELECT COUNT(*) AS total FROM doctor'),
		'Departments' => count_rows('SELECT COUNT(*) AS total FROM department'),
		'Drugs' => count_rows('SELECT COUNT(*) AS total FROM drug'),
		'Allergies' => count_rows('SELECT COUNT(*) AS total FROM patient_allergy'),
	];

	$latestHospitalizations = fetch_all(
		'SELECT h.id, h.admission_date, h.discharge_date, p.first_name, p.last_name, d.name AS department_name, h.ken_code
		 FROM hospitalization h
		 JOIN patient p ON p.amka = h.patient_amka
		 JOIN department d ON d.id = h.department_id
		 ORDER BY h.admission_date DESC, h.id DESC
		 LIMIT 8'
	);

	$recentPatients = fetch_all(
		'SELECT amka, first_name, last_name, insurance
		 FROM patient
		 ORDER BY last_name, first_name
		 LIMIT 8'
	);

	render_header('dashboard');
	?>
	<div class="grid cols-3">
		<?php foreach ($counts as $label => $value): ?>
			<div class="card kpi">
				<span><?= h($label) ?></span>
				<strong><?= h(number_format((int) $value)) ?></strong>
			</div>
		<?php endforeach; ?>
	</div>

	<div style="height: 20px"></div>

	<div class="split">
		<section class="panel">
			<div class="section-head">
				<div>
					<h2>Latest hospitalizations</h2>
					<p>Joined view across patient and department data.</p>
				</div>
				<a class="button secondary" href="?page=hospitalizations">Open list</a>
			</div>
			<div class="overflow">
				<table>
					<thead>
					<tr>
						<th>ID</th>
						<th>Patient</th>
						<th>Department</th>
						<th>Admission</th>
						<th>Discharge</th>
						<th>KEN</th>
					</tr>
					</thead>
					<tbody>
					<?php foreach ($latestHospitalizations as $row): ?>
						<tr>
							<td><a href="?page=hospitalization&id=<?= h($row['id']) ?>"><?= h($row['id']) ?></a></td>
							<td><?= h($row['first_name'] . ' ' . $row['last_name']) ?></td>
							<td><?= h($row['department_name']) ?></td>
							<td><?= h($row['admission_date']) ?></td>
							<td><?= h($row['discharge_date'] ?? 'Open') ?></td>
							<td><?= h($row['ken_code']) ?></td>
						</tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			</div>
		</section>

		<aside class="grid-list">
			<div class="panel">
				<div class="section-head">
					<div>
						<h2>Quick actions</h2>
						<p>Start with the most common records.</p>
					</div>
				</div>
				<div class="actions">
					<a class="button" href="?page=patient-new">New patient</a>
					<a class="button secondary" href="?page=department-new">New department</a>
					<a class="button secondary" href="?page=search">Search data</a>
				</div>
			</div>

			<div class="panel">
				<div class="section-head">
					<div>
						<h2>Recent patients</h2>
						<p>Open a profile to see history and allergies.</p>
					</div>
				</div>
				<div class="stack">
					<?php foreach ($recentPatients as $row): ?>
						<div class="badge">
							<a href="?page=patient&id=<?= h($row['amka']) ?>"><?= h($row['first_name'] . ' ' . $row['last_name']) ?></a>
							<span class="muted">·</span>
							<span><?= h($row['insurance']) ?></span>
						</div>
					<?php endforeach; ?>
				</div>
			</div>
		</aside>
	</div>
	<?php
	render_footer();
}

function patient_form_defaults(?array $patient = null): array
{
	return array_merge([
		'amka' => '',
		'first_name' => '',
		'last_name' => '',
		'fathers_name' => '',
		'birth_date' => '',
		'gender' => 'M',
		'weight_kg' => '',
		'height_cm' => '',
		'address' => '',
		'phone' => '',
		'email' => '',
		'occupation' => '',
		'nationality' => '',
		'emergency_name' => '',
		'emergency_phone' => '',
		'emergency_rel' => '',
		'insurance' => 'EFKA',
	], $patient ?? []);
}

function patient_save(): void
{
	if (request_method() !== 'POST') {
		redirect_to(['page' => 'patients']);
	}

	$data = [
		'amka' => trim((string) param('amka', '')),
		'first_name' => trim((string) param('first_name', '')),
		'last_name' => trim((string) param('last_name', '')),
		'fathers_name' => trim((string) param('fathers_name', '')),
		'birth_date' => trim((string) param('birth_date', '')),
		'gender' => trim((string) param('gender', '')),
		'weight_kg' => trim((string) param('weight_kg', '')),
		'height_cm' => trim((string) param('height_cm', '')),
		'address' => trim((string) param('address', '')),
		'phone' => trim((string) param('phone', '')),
		'email' => trim((string) param('email', '')),
		'occupation' => trim((string) param('occupation', '')),
		'nationality' => trim((string) param('nationality', '')),
		'emergency_name' => trim((string) param('emergency_name', '')),
		'emergency_phone' => trim((string) param('emergency_phone', '')),
		'emergency_rel' => trim((string) param('emergency_rel', '')),
		'insurance' => trim((string) param('insurance', '')),
	];

	foreach (['amka', 'first_name', 'last_name', 'fathers_name', 'birth_date', 'gender', 'insurance'] as $required) {
		if ($data[$required] === '') {
			flash_set('error', 'Patient save failed: missing required field ' . $required . '.');
			redirect_to(['page' => 'patient-new']);
		}
	}

	$allowedGenders = ['M', 'F', 'O'];
	$allowedInsurance = ['EFKA', 'Private', 'Uninsured', 'Other'];
	if (!in_array($data['gender'], $allowedGenders, true) || !in_array($data['insurance'], $allowedInsurance, true)) {
		flash_set('error', 'Patient save failed: invalid gender or insurance value.');
		redirect_to(['page' => 'patient-new']);
	}

	$isEdit = trim((string) param('mode', 'new')) === 'edit';

	try {
		if ($isEdit) {
			execute_sql(
				'UPDATE patient
				 SET first_name = :first_name,
					 last_name = :last_name,
					 fathers_name = :fathers_name,
					 birth_date = :birth_date,
					 gender = :gender,
					 weight_kg = :weight_kg,
					 height_cm = :height_cm,
					 address = :address,
					 phone = :phone,
					 email = :email,
					 occupation = :occupation,
					 nationality = :nationality,
					 emergency_name = :emergency_name,
					 emergency_phone = :emergency_phone,
					 emergency_rel = :emergency_rel,
					 insurance = :insurance
				 WHERE amka = :amka',
				[
					':amka' => $data['amka'],
					':first_name' => $data['first_name'],
					':last_name' => $data['last_name'],
					':fathers_name' => $data['fathers_name'],
					':birth_date' => $data['birth_date'],
					':gender' => $data['gender'],
					':weight_kg' => $data['weight_kg'] !== '' ? $data['weight_kg'] : null,
					':height_cm' => $data['height_cm'] !== '' ? $data['height_cm'] : null,
					':address' => $data['address'] !== '' ? $data['address'] : null,
					':phone' => $data['phone'] !== '' ? $data['phone'] : null,
					':email' => $data['email'] !== '' ? $data['email'] : null,
					':occupation' => $data['occupation'] !== '' ? $data['occupation'] : null,
					':nationality' => $data['nationality'] !== '' ? $data['nationality'] : null,
					':emergency_name' => $data['emergency_name'] !== '' ? $data['emergency_name'] : null,
					':emergency_phone' => $data['emergency_phone'] !== '' ? $data['emergency_phone'] : null,
					':emergency_rel' => $data['emergency_rel'] !== '' ? $data['emergency_rel'] : null,
					':insurance' => $data['insurance'],
				]
			);
			flash_set('success', 'Patient updated.');
			redirect_to(['page' => 'patient', 'id' => $data['amka']]);
		}

		execute_sql(
			'INSERT INTO patient
			(amka, first_name, last_name, fathers_name, birth_date, gender, weight_kg, height_cm, address, phone, email, occupation, nationality, emergency_name, emergency_phone, emergency_rel, insurance)
			VALUES
			(:amka, :first_name, :last_name, :fathers_name, :birth_date, :gender, :weight_kg, :height_cm, :address, :phone, :email, :occupation, :nationality, :emergency_name, :emergency_phone, :emergency_rel, :insurance)',
			[
				':amka' => $data['amka'],
				':first_name' => $data['first_name'],
				':last_name' => $data['last_name'],
				':fathers_name' => $data['fathers_name'],
				':birth_date' => $data['birth_date'],
				':gender' => $data['gender'],
				':weight_kg' => $data['weight_kg'] !== '' ? $data['weight_kg'] : null,
				':height_cm' => $data['height_cm'] !== '' ? $data['height_cm'] : null,
				':address' => $data['address'] !== '' ? $data['address'] : null,
				':phone' => $data['phone'] !== '' ? $data['phone'] : null,
				':email' => $data['email'] !== '' ? $data['email'] : null,
				':occupation' => $data['occupation'] !== '' ? $data['occupation'] : null,
				':nationality' => $data['nationality'] !== '' ? $data['nationality'] : null,
				':emergency_name' => $data['emergency_name'] !== '' ? $data['emergency_name'] : null,
				':emergency_phone' => $data['emergency_phone'] !== '' ? $data['emergency_phone'] : null,
				':emergency_rel' => $data['emergency_rel'] !== '' ? $data['emergency_rel'] : null,
				':insurance' => $data['insurance'],
			]
		);
		flash_set('success', 'Patient created.');
		redirect_to(['page' => 'patient', 'id' => $data['amka']]);
	} catch (Throwable $exception) {
		flash_set('error', 'Patient save failed: ' . $exception->getMessage());
		redirect_to(['page' => $isEdit ? 'patient-edit' : 'patient-new', 'id' => $data['amka']]);
	}
}

function patient_delete(): void
{
	if (request_method() !== 'POST') {
		redirect_to(['page' => 'patients']);
	}

	$amka = trim((string) param('amka', ''));
	if ($amka === '') {
		flash_set('error', 'Missing patient identifier.');
		redirect_to(['page' => 'patients']);
	}

	try {
		execute_sql('DELETE FROM patient WHERE amka = :amka', [':amka' => $amka]);
		flash_set('success', 'Patient deleted.');
	} catch (Throwable $exception) {
		flash_set('error', 'Patient deletion failed: ' . $exception->getMessage());
	}

	redirect_to(['page' => 'patients']);
}

function patient_list_page(): void
{
	$q = trim((string) param('q', ''));
	$limit = safe_limit_value(param('limit', 25));
	$params = [];
	$where = '';
	if ($q !== '') {
		$where = 'WHERE p.amka LIKE :amka_query OR p.first_name LIKE :first_name_query OR p.last_name LIKE :last_name_query OR p.email LIKE :email_query';
		$params[':amka_query'] = '%' . $q . '%';
		$params[':first_name_query'] = '%' . $q . '%';
		$params[':last_name_query'] = '%' . $q . '%';
		$params[':email_query'] = '%' . $q . '%';
	}

	$patients = fetch_all(
		'SELECT p.*,
				COUNT(DISTINCT h.id) AS hospitalization_count,
				COUNT(DISTINCT pa.substance_id) AS allergy_count
		 FROM patient p
		 LEFT JOIN hospitalization h ON h.patient_amka = p.amka
		 LEFT JOIN patient_allergy pa ON pa.patient_amka = p.amka
		 ' . $where . '
		 GROUP BY p.amka
		 ORDER BY p.last_name, p.first_name
		 LIMIT ' . (int) $limit,
		$params
	);

	render_header('patients');
	?>
	<div class="section-head">
		<div>
			<h1>Patients</h1>
			<p>Search, inspect, and manage patient records directly in MariaDB.</p>
		</div>
		<a class="button" href="?page=patient-new">New patient</a>
	</div>

	<div class="panel">
		<form method="get" class="form-grid">
			<input type="hidden" name="page" value="patients">
			<div>
				<label for="q">Search</label>
				<input id="q" name="q" value="<?= h($q) ?>" placeholder="AMKA, name, or email">
			</div>
			<div>
				<label for="limit">Rows</label>
				<select id="limit" name="limit">
					<?php foreach ([10, 25, 50, 100] as $option): ?>
						<option value="<?= h($option) ?>" <?= selected((string) $option, (string) $limit) ?>><?= h($option) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div class="full actions">
				<input type="submit" value="Apply filters">
				<a class="button secondary" href="?page=patients">Reset</a>
			</div>
		</form>
	</div>

	<div style="height: 18px"></div>

	<div class="panel overflow">
		<table>
			<thead>
			<tr>
				<th>AMKA</th>
				<th>Name</th>
				<th>Birth</th>
				<th>Insurance</th>
				<th>Hospitalizations</th>
				<th>Allergies</th>
				<th></th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($patients as $row): ?>
				<tr>
					<td><?= h($row['amka']) ?></td>
					<td><?= h($row['last_name'] . ', ' . $row['first_name']) ?></td>
					<td><?= h($row['birth_date']) ?></td>
					<td><?= h($row['insurance']) ?></td>
					<td><?= h($row['hospitalization_count']) ?></td>
					<td><?= h($row['allergy_count']) ?></td>
					<td class="actions">
						<a class="button secondary" href="?page=patient&id=<?= h($row['amka']) ?>">Open</a>
						<a class="button secondary" href="?page=patient-edit&id=<?= h($row['amka']) ?>">Edit</a>
					</td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</div>
	<?php
	render_footer();
}

function patient_detail_page(): void
{
	$amka = trim((string) param('id', ''));
	$patient = fetch_one('SELECT * FROM patient WHERE amka = :amka', [':amka' => $amka]);
	if ($patient === null) {
		flash_set('error', 'Patient not found.');
		redirect_to(['page' => 'patients']);
	}

	$hospitalizations = fetch_all(
		'SELECT h.id, h.admission_date, h.discharge_date, h.admission_icd10, h.discharge_icd10, h.ken_code, d.name AS department_name, b.bed_number
		 FROM hospitalization h
		 JOIN department d ON d.id = h.department_id
		 JOIN bed b ON b.id = h.bed_id
		 WHERE h.patient_amka = :amka
		 ORDER BY h.admission_date DESC, h.id DESC',
		[':amka' => $amka]
	);

	$allergies = fetch_all(
		'SELECT pa.substance_id, pa.notes, s.name AS substance_name
		 FROM patient_allergy pa
		 JOIN active_substance s ON s.id = pa.substance_id
		 WHERE pa.patient_amka = :amka
		 ORDER BY s.name',
		[':amka' => $amka]
	);

	$reviews = fetch_all(
		'SELECT id, hospitalization_id, medical_care, review_date
		 FROM patient_review_doctor
		 WHERE patient_amka = :amka
		 ORDER BY review_date DESC
		 LIMIT 10',
		[':amka' => $amka]
	);

	$substances = fetch_all('SELECT id, name FROM active_substance ORDER BY name LIMIT 500');

	render_header('patient');
	?>
	<div class="section-head">
		<div>
			<h1><?= h($patient['last_name'] . ', ' . $patient['first_name']) ?></h1>
			<p>AMKA <?= h($patient['amka']) ?> · <?= h($patient['insurance']) ?> · <?= h($patient['gender']) ?></p>
		</div>
		<div class="actions">
			<a class="button secondary" href="?page=patient-edit&id=<?= h($patient['amka']) ?>">Edit patient</a>
			<form method="post" action="?page=patient-delete" onsubmit="return confirm('Delete this patient?');" style="margin:0;">
				<input type="hidden" name="amka" value="<?= h($patient['amka']) ?>">
				<input type="submit" class="danger" value="Delete">
			</form>
		</div>
	</div>

	<div class="grid cols-2">
		<section class="panel">
			<h2>Profile</h2>
			<div class="grid cols-2" style="margin-top: 14px;">
				<div class="card"><span class="muted">Father's name</span><div><?= h($patient['fathers_name']) ?></div></div>
				<div class="card"><span class="muted">Birth date</span><div><?= h($patient['birth_date']) ?></div></div>
				<div class="card"><span class="muted">Weight</span><div><?= h($patient['weight_kg'] ?? 'n/a') ?></div></div>
				<div class="card"><span class="muted">Height</span><div><?= h($patient['height_cm'] ?? 'n/a') ?></div></div>
				<div class="card full"><span class="muted">Contact</span><div><?= h($patient['phone'] ?? 'n/a') ?> · <?= h($patient['email'] ?? 'n/a') ?></div></div>
				<div class="card full"><span class="muted">Address</span><div><?= h($patient['address'] ?? 'n/a') ?></div></div>
			</div>
		</section>

		<section class="panel">
			<div class="section-head">
				<div>
					<h2>Allergies</h2>
					<p>Add a recorded active substance allergy.</p>
				</div>
			</div>
			<form method="post" action="?page=patient-allergy-add" class="stack">
				<input type="hidden" name="patient_amka" value="<?= h($patient['amka']) ?>">
				<label for="substance_id">Active substance</label>
				<select id="substance_id" name="substance_id" required>
					<option value="">Choose one</option>
					<?php foreach ($substances as $substance): ?>
						<option value="<?= h($substance['id']) ?>"><?= h($substance['name']) ?></option>
					<?php endforeach; ?>
				</select>
				<label for="notes">Notes</label>
				<textarea id="notes" name="notes" placeholder="Optional notes"></textarea>
				<input type="submit" value="Add allergy">
			</form>

			<div style="height: 16px"></div>
			<div class="stack">
				<?php foreach ($allergies as $allergy): ?>
					<div class="badge warn">
						<?= h($allergy['substance_name']) ?>
						<?php if (!empty($allergy['notes'])): ?>
							<span class="muted">·</span>
							<span><?= h($allergy['notes']) ?></span>
						<?php endif; ?>
					</div>
				<?php endforeach; ?>
				<?php if ($allergies === []): ?>
					<p>No allergies recorded.</p>
				<?php endif; ?>
			</div>
		</section>
	</div>

	<div style="height: 18px"></div>

	<section class="panel">
		<div class="section-head">
			<div>
				<h2>Hospitalization history</h2>
				<p>Current and past stays with ICD-10 and KEN codes.</p>
			</div>
		</div>
		<div class="overflow">
			<table>
				<thead>
				<tr>
					<th>ID</th>
					<th>Department</th>
					<th>Bed</th>
					<th>Admission</th>
					<th>Discharge</th>
					<th>ICD-10</th>
					<th>KEN</th>
				</tr>
				</thead>
				<tbody>
				<?php foreach ($hospitalizations as $row): ?>
					<tr>
						<td><a href="?page=hospitalization&id=<?= h($row['id']) ?>"><?= h($row['id']) ?></a></td>
						<td><?= h($row['department_name']) ?></td>
						<td><?= h($row['bed_number']) ?></td>
						<td><?= h($row['admission_date']) ?></td>
						<td><?= h($row['discharge_date'] ?? 'Open') ?></td>
						<td><?= h($row['admission_icd10']) ?></td>
						<td><?= h($row['ken_code']) ?></td>
					</tr>
				<?php endforeach; ?>
				</tbody>
			</table>
		</div>
	</section>

	<div style="height: 18px"></div>

	<section class="panel">
		<div class="section-head">
			<div>
				<h2>Doctor reviews</h2>
				<p>Latest review records linked to this patient.</p>
			</div>
		</div>
		<div class="overflow">
			<table>
				<thead>
				<tr>
					<th>Review ID</th>
					<th>Hospitalization</th>
					<th>Medical care</th>
					<th>Review date</th>
				</tr>
				</thead>
				<tbody>
				<?php foreach ($reviews as $row): ?>
					<tr>
						<td><?= h($row['id']) ?></td>
						<td><a href="?page=hospitalization&id=<?= h($row['hospitalization_id']) ?>"><?= h($row['hospitalization_id']) ?></a></td>
						<td><?= h($row['medical_care']) ?></td>
						<td><?= h($row['review_date']) ?></td>
					</tr>
				<?php endforeach; ?>
				<?php if ($reviews === []): ?>
					<tr><td colspan="4" class="muted">No doctor review records found.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
		</div>
	</section>
	<?php
	render_footer();
}

function patient_edit_page(): void
{
	$amka = trim((string) param('id', ''));
	$patient = fetch_one('SELECT * FROM patient WHERE amka = :amka', [':amka' => $amka]);
	if ($patient === null) {
		flash_set('error', 'Patient not found.');
		redirect_to(['page' => 'patients']);
	}

	$defaults = patient_form_defaults($patient);

	render_header('patient-edit');
	?>
	<div class="section-head">
		<div>
			<h1>Edit patient</h1>
			<p>Update the patient profile without touching the relational model.</p>
		</div>
	</div>

	<section class="panel">
		<form method="post" action="?page=patient-save" class="form-grid">
			<input type="hidden" name="mode" value="edit">
			<div>
				<label for="amka">AMKA</label>
				<input id="amka" name="amka" value="<?= h($defaults['amka']) ?>" readonly>
			</div>
			<div>
				<label for="insurance">Insurance</label>
				<select id="insurance" name="insurance">
					<?php foreach (['EFKA', 'Private', 'Uninsured', 'Other'] as $option): ?>
						<option value="<?= h($option) ?>" <?= selected($option, $defaults['insurance']) ?>><?= h($option) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<?php foreach (['first_name' => 'First name', 'last_name' => 'Last name', 'fathers_name' => "Father's name", 'birth_date' => 'Birth date', 'weight_kg' => 'Weight (kg)', 'height_cm' => 'Height (cm)', 'address' => 'Address', 'phone' => 'Phone', 'email' => 'Email', 'occupation' => 'Occupation', 'nationality' => 'Nationality', 'emergency_name' => 'Emergency contact', 'emergency_phone' => 'Emergency phone', 'emergency_rel' => 'Emergency relationship'] as $field => $label): ?>
				<div class="<?= in_array($field, ['address', 'email', 'occupation', 'nationality', 'emergency_name', 'emergency_phone', 'emergency_rel'], true) ? 'full' : '' ?>">
					<label for="<?= h($field) ?>"><?= h($label) ?></label>
					<input id="<?= h($field) ?>" name="<?= h($field) ?>" value="<?= h($defaults[$field]) ?>"<?= $field === 'birth_date' ? ' type="date"' : '' ?>>
				</div>
			<?php endforeach; ?>
			<div>
				<label for="gender">Gender</label>
				<select id="gender" name="gender">
					<?php foreach (['M' => 'Male', 'F' => 'Female', 'O' => 'Other'] as $value => $label): ?>
						<option value="<?= h($value) ?>" <?= selected($value, $defaults['gender']) ?>><?= h($label) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div class="full actions">
				<input type="submit" value="Save changes">
				<a class="button secondary" href="?page=patient&id=<?= h($defaults['amka']) ?>">Cancel</a>
			</div>
		</form>
	</section>
	<?php
	render_footer();
}

function patient_new_page(): void
{
	$defaults = patient_form_defaults();
	render_header('patient-new');
	?>
	<div class="section-head">
		<div>
			<h1>New patient</h1>
			<p>Create a patient record using the live schema.</p>
		</div>
	</div>

	<section class="panel">
		<form method="post" action="?page=patient-save" class="form-grid">
			<input type="hidden" name="mode" value="new">
			<?php foreach (['amka' => 'AMKA', 'first_name' => 'First name', 'last_name' => 'Last name', 'fathers_name' => "Father's name", 'birth_date' => 'Birth date', 'weight_kg' => 'Weight (kg)', 'height_cm' => 'Height (cm)', 'address' => 'Address', 'phone' => 'Phone', 'email' => 'Email', 'occupation' => 'Occupation', 'nationality' => 'Nationality', 'emergency_name' => 'Emergency contact', 'emergency_phone' => 'Emergency phone', 'emergency_rel' => 'Emergency relationship'] as $field => $label): ?>
				<div class="<?= in_array($field, ['amka', 'address', 'email', 'occupation', 'nationality', 'emergency_name', 'emergency_phone', 'emergency_rel'], true) ? 'full' : '' ?>">
					<label for="<?= h($field) ?>"><?= h($label) ?></label>
					<input id="<?= h($field) ?>" name="<?= h($field) ?>" value="<?= h($defaults[$field]) ?>"<?= $field === 'birth_date' ? ' type="date"' : '' ?>>
				</div>
			<?php endforeach; ?>
			<div>
				<label for="gender">Gender</label>
				<select id="gender" name="gender">
					<?php foreach (['M' => 'Male', 'F' => 'Female', 'O' => 'Other'] as $value => $label): ?>
						<option value="<?= h($value) ?>" <?= selected($value, $defaults['gender']) ?>><?= h($label) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div>
				<label for="insurance">Insurance</label>
				<select id="insurance" name="insurance">
					<?php foreach (['EFKA', 'Private', 'Uninsured', 'Other'] as $option): ?>
						<option value="<?= h($option) ?>" <?= selected($option, $defaults['insurance']) ?>><?= h($option) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div class="full actions">
				<input type="submit" value="Create patient">
				<a class="button secondary" href="?page=patients">Cancel</a>
			</div>
		</form>
	</section>
	<?php
	render_footer();
}

function patient_allergy_add(): void
{
	if (request_method() !== 'POST') {
		redirect_to(['page' => 'patients']);
	}

	$patientAmka = trim((string) param('patient_amka', ''));
	$substanceId = (int) param('substance_id', 0);
	$notes = trim((string) param('notes', ''));

	if ($patientAmka === '' || $substanceId <= 0) {
		flash_set('error', 'Allergy save failed: choose a patient and a substance.');
		redirect_to(['page' => 'patient', 'id' => $patientAmka]);
	}

	try {
		execute_sql(
			'INSERT INTO patient_allergy (patient_amka, substance_id, notes)
			 VALUES (:patient_amka, :substance_id, :notes)
			 ON DUPLICATE KEY UPDATE notes = VALUES(notes)',
			[
				':patient_amka' => $patientAmka,
				':substance_id' => $substanceId,
				':notes' => $notes !== '' ? $notes : null,
			]
		);
		flash_set('success', 'Allergy recorded.');
	} catch (Throwable $exception) {
		flash_set('error', 'Allergy save failed: ' . $exception->getMessage());
	}

	redirect_to(['page' => 'patient', 'id' => $patientAmka]);
}

function department_list_page(): void
{
	$q = trim((string) param('q', ''));
	$limit = safe_limit_value(param('limit', 25));
	$params = [];
	$where = '';
	if ($q !== '') {
		$where = 'WHERE d.name LIKE :dept_name_query OR d.description LIKE :dept_description_query OR s.first_name LIKE :director_first_query OR s.last_name LIKE :director_last_query';
		$params = [
			':dept_name_query' => '%' . $q . '%',
			':dept_description_query' => '%' . $q . '%',
			':director_first_query' => '%' . $q . '%',
			':director_last_query' => '%' . $q . '%',
		];
	}

	$departments = fetch_all(
		'SELECT d.*, CONCAT(s.first_name, " ", s.last_name) AS director_name,
				COUNT(DISTINCT b.id) AS bed_total,
				COUNT(DISTINCT doc.doctor_amka) AS doctor_links,
				COUNT(DISTINCT n.amka) AS nurse_total,
				COUNT(DISTINCT a.amka) AS admin_total
		 FROM department d
		 LEFT JOIN doctor dir ON dir.amka = d.director_amka
		 LEFT JOIN staff s ON s.amka = dir.amka
		 LEFT JOIN bed b ON b.department_id = d.id
		 LEFT JOIN doctor_department doc ON doc.department_id = d.id
		 LEFT JOIN nurse n ON n.department_id = d.id
		 LEFT JOIN admin_staff a ON a.department_id = d.id
		 ' . $where . '
		 GROUP BY d.id
		 ORDER BY d.name
		 LIMIT ' . (int) $limit,
		$params
	);

	render_header('departments');
	?>
	<div class="section-head">
		<div>
			<h1>Departments</h1>
			<p>Operational overview of bed capacity and staffing links.</p>
		</div>
		<a class="button" href="?page=department-new">New department</a>
	</div>

	<div class="panel">
		<form method="get" class="form-grid">
			<input type="hidden" name="page" value="departments">
			<div>
				<label for="q">Search</label>
				<input id="q" name="q" value="<?= h($q) ?>" placeholder="name, description, or director">
			</div>
			<div>
				<label for="limit">Rows</label>
				<select id="limit" name="limit">
					<?php foreach ([10, 25, 50, 100] as $option): ?>
						<option value="<?= h($option) ?>" <?= selected((string) $option, (string) $limit) ?>><?= h($option) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div class="full actions">
				<input type="submit" value="Apply filters">
				<a class="button secondary" href="?page=departments">Reset</a>
			</div>
		</form>
	</div>

	<div style="height: 18px"></div>
	<div class="panel overflow">
		<table>
			<thead>
			<tr>
				<th>Name</th>
				<th>Director</th>
				<th>Beds</th>
				<th>Doctors</th>
				<th>Nurses</th>
				<th>Admins</th>
				<th></th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($departments as $row): ?>
				<tr class="row-selectable" tabindex="0" data-row-select="1" data-href="?page=department&id=<?= h($row['id']) ?>">
					<td><?= h($row['name']) ?></td>
					<td><?= h($row['director_name'] ?? 'Unassigned') ?></td>
					<td><?= h($row['bed_total']) ?></td>
					<td><?= h($row['doctor_links']) ?></td>
					<td><?= h($row['nurse_total']) ?></td>
					<td><?= h($row['admin_total']) ?></td>
					<td class="actions">
						<a class="button secondary" href="?page=department&id=<?= h($row['id']) ?>">Open</a>
						<a class="button secondary" href="?page=department-edit&id=<?= h($row['id']) ?>">Edit</a>
					</td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</div>
	<?php
	render_footer();
}

function department_form_defaults(?array $department = null): array
{
	return array_merge([
		'id' => '',
		'name' => '',
		'description' => '',
		'bed_count' => '',
		'floor_building' => '',
		'director_amka' => '',
	], $department ?? []);
}

function department_save(): void
{
	if (request_method() !== 'POST') {
		redirect_to(['page' => 'departments']);
	}

	$data = [
		'id' => trim((string) param('id', '')),
		'name' => trim((string) param('name', '')),
		'description' => trim((string) param('description', '')),
		'bed_count' => (int) param('bed_count', 0),
		'floor_building' => trim((string) param('floor_building', '')),
		'director_amka' => trim((string) param('director_amka', '')),
	];

	if ($data['name'] === '') {
		flash_set('error', 'Department save failed: name is required.');
		redirect_to(['page' => 'department-new']);
	}

	$isEdit = trim((string) param('mode', 'new')) === 'edit';

	try {
		if ($isEdit) {
			execute_sql(
				'UPDATE department
				 SET name = :name,
					 description = :description,
					 bed_count = :bed_count,
					 floor_building = :floor_building,
					 director_amka = :director_amka
				 WHERE id = :id',
				[
					':id' => (int) $data['id'],
					':name' => $data['name'],
					':description' => $data['description'] !== '' ? $data['description'] : null,
					':bed_count' => $data['bed_count'],
					':floor_building' => $data['floor_building'] !== '' ? $data['floor_building'] : null,
					':director_amka' => $data['director_amka'] !== '' ? $data['director_amka'] : null,
				]
			);
			flash_set('success', 'Department updated.');
			redirect_to(['page' => 'department', 'id' => (int) $data['id']]);
		}

		execute_sql(
			'INSERT INTO department (name, description, bed_count, floor_building, director_amka)
			 VALUES (:name, :description, :bed_count, :floor_building, :director_amka)',
			[
				':name' => $data['name'],
				':description' => $data['description'] !== '' ? $data['description'] : null,
				':bed_count' => $data['bed_count'],
				':floor_building' => $data['floor_building'] !== '' ? $data['floor_building'] : null,
				':director_amka' => $data['director_amka'] !== '' ? $data['director_amka'] : null,
			]
		);
		$newId = (int) (pdo()?->lastInsertId() ?? 0);
		flash_set('success', 'Department created.');
		redirect_to(['page' => 'department', 'id' => $newId]);
	} catch (Throwable $exception) {
		flash_set('error', 'Department save failed: ' . $exception->getMessage());
		redirect_to(['page' => $isEdit ? 'department-edit' : 'department-new', 'id' => $data['id']]);
	}
}

function department_detail_page(): void
{
	$id = (int) param('id', 0);
	$department = fetch_one('SELECT * FROM department WHERE id = :id', [':id' => $id]);
	if ($department === null) {
		flash_set('error', 'Department not found.');
		redirect_to(['page' => 'departments']);
	}

	$beds = fetch_all(
		'SELECT id, bed_number, bed_type, status
		 FROM bed
		 WHERE department_id = :id
		 ORDER BY bed_number',
		[':id' => $id]
	);

	$staff = fetch_all(
		'SELECT s.amka, s.first_name, s.last_name, s.staff_type,
				d.specialty, d.rank AS doctor_rank,
				n.rank AS nurse_rank,
				a.role AS admin_role
		 FROM staff s
		 LEFT JOIN doctor d ON d.amka = s.amka
		 LEFT JOIN nurse n ON n.amka = s.amka
		 LEFT JOIN admin_staff a ON a.amka = s.amka
		 WHERE EXISTS (
			 SELECT 1 FROM doctor_department dd WHERE dd.doctor_amka = s.amka AND dd.department_id = :doctor_dept_id
		 )
		 OR EXISTS (
			 SELECT 1 FROM nurse n2 WHERE n2.amka = s.amka AND n2.department_id = :nurse_dept_id
		 )
		 OR EXISTS (
			 SELECT 1 FROM admin_staff a2 WHERE a2.amka = s.amka AND a2.department_id = :admin_dept_id
		 )
		 ORDER BY s.last_name, s.first_name',
		[
			':doctor_dept_id' => $id,
			':nurse_dept_id' => $id,
			':admin_dept_id' => $id,
		]
	);

	render_header('department');
	?>
	<div class="section-head">
		<div>
			<h1><?= h($department['name']) ?></h1>
			<p><?= h($department['description'] ?? 'No description') ?></p>
		</div>
		<div class="actions">
			<a class="button secondary" href="?page=department-edit&id=<?= h($department['id']) ?>">Edit department</a>
		</div>
	</div>

	<div class="grid cols-2">
		<section class="panel">
			<h2>Department summary</h2>
			<div class="grid cols-2" style="margin-top: 14px;">
				<div class="card"><span class="muted">Beds (planned)</span><div><?= h($department['bed_count']) ?></div></div>
				<div class="card"><span class="muted">Building / floor</span><div><?= h($department['floor_building'] ?? 'n/a') ?></div></div>
				<div class="card full"><span class="muted">Director AMKA</span><div><?= h($department['director_amka'] ?? 'n/a') ?></div></div>
			</div>
		</section>

		<section class="panel">
			<h2>Bed inventory</h2>
			<div class="overflow" style="margin-top: 14px;">
				<table>
					<thead>
					<tr>
						<th>Bed</th>
						<th>Type</th>
						<th>Status</th>
					</tr>
					</thead>
					<tbody>
					<?php foreach ($beds as $row): ?>
						<tr>
							<td><?= h($row['bed_number']) ?></td>
							<td><?= h($row['bed_type']) ?></td>
							<td><?= h($row['status']) ?></td>
						</tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			</div>
		</section>
	</div>

	<div style="height: 18px"></div>

	<section class="panel">
		<h2>Assigned staff</h2>
		<div class="overflow" style="margin-top: 14px;">
			<table>
				<thead>
				<tr>
					<th>Name</th>
					<th>Type</th>
					<th>Specialty / role</th>
				</tr>
				</thead>
				<tbody>
				<?php foreach ($staff as $row): ?>
					<tr>
						<td><?= h($row['last_name'] . ', ' . $row['first_name']) ?></td>
						<td><?= h($row['staff_type']) ?></td>
						<td><?= h($row['specialty'] ?? $row['nurse_rank'] ?? $row['admin_role'] ?? 'n/a') ?></td>
					</tr>
				<?php endforeach; ?>
				<?php if ($staff === []): ?>
					<tr><td colspan="3" class="muted">No staff assignments found.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
		</div>
	</section>
	<?php
	render_footer();
}

function department_edit_page(): void
{
	$id = (int) param('id', 0);
	$department = fetch_one('SELECT * FROM department WHERE id = :id', [':id' => $id]);
	if ($department === null) {
		flash_set('error', 'Department not found.');
		redirect_to(['page' => 'departments']);
	}

	$defaults = department_form_defaults($department);
	render_header('department-edit');
	?>
	<div class="section-head">
		<div>
			<h1>Edit department</h1>
			<p>Update the department metadata and director assignment.</p>
		</div>
	</div>
	<section class="panel">
		<form method="post" action="?page=department-save" class="form-grid">
			<input type="hidden" name="mode" value="edit">
			<div>
				<label for="id">ID</label>
				<input id="id" name="id" value="<?= h($defaults['id']) ?>" readonly>
			</div>
			<div>
				<label for="name">Name</label>
				<input id="name" name="name" value="<?= h($defaults['name']) ?>">
			</div>
			<div>
				<label for="bed_count">Bed count</label>
				<input id="bed_count" name="bed_count" type="number" min="0" value="<?= h($defaults['bed_count']) ?>">
			</div>
			<div>
				<label for="floor_building">Floor / building</label>
				<input id="floor_building" name="floor_building" value="<?= h($defaults['floor_building']) ?>">
			</div>
			<div>
				<label for="director_amka">Director AMKA</label>
				<input id="director_amka" name="director_amka" value="<?= h($defaults['director_amka']) ?>">
			</div>
			<div class="full">
				<label for="description">Description</label>
				<textarea id="description" name="description"><?= h($defaults['description']) ?></textarea>
			</div>
			<div class="full actions">
				<input type="submit" value="Save changes">
				<a class="button secondary" href="?page=department&id=<?= h($defaults['id']) ?>">Cancel</a>
			</div>
		</form>
	</section>
	<?php
	render_footer();
}

function department_new_page(): void
{
	$defaults = department_form_defaults();
	render_header('department-new');
	?>
	<div class="section-head">
		<div>
			<h1>New department</h1>
			<p>Create a department entry for the live hospital model.</p>
		</div>
	</div>
	<section class="panel">
		<form method="post" action="?page=department-save" class="form-grid">
			<input type="hidden" name="mode" value="new">
			<div>
				<label for="name">Name</label>
				<input id="name" name="name" value="<?= h($defaults['name']) ?>">
			</div>
			<div>
				<label for="bed_count">Bed count</label>
				<input id="bed_count" name="bed_count" type="number" min="0" value="<?= h($defaults['bed_count'] ?: 0) ?>">
			</div>
			<div>
				<label for="floor_building">Floor / building</label>
				<input id="floor_building" name="floor_building" value="<?= h($defaults['floor_building']) ?>">
			</div>
			<div>
				<label for="director_amka">Director AMKA</label>
				<input id="director_amka" name="director_amka" value="<?= h($defaults['director_amka']) ?>">
			</div>
			<div class="full">
				<label for="description">Description</label>
				<textarea id="description" name="description"><?= h($defaults['description']) ?></textarea>
			</div>
			<div class="full actions">
				<input type="submit" value="Create department">
				<a class="button secondary" href="?page=departments">Cancel</a>
			</div>
		</form>
	</section>
	<?php
	render_footer();
}

function hospitalization_list_page(): void
{
	$hospitalizations = fetch_all(
		'SELECT h.id, h.patient_amka, h.admission_date, h.discharge_date, h.admission_icd10, h.discharge_icd10, h.ken_code,
				p.first_name, p.last_name, d.name AS department_name, b.bed_number
		 FROM hospitalization h
		 JOIN patient p ON p.amka = h.patient_amka
		 JOIN department d ON d.id = h.department_id
		 JOIN bed b ON b.id = h.bed_id
		 ORDER BY h.admission_date DESC, h.id DESC
		 LIMIT 100'
	);

	render_header('hospitalizations');
	?>
	<div class="section-head">
		<div>
			<h1>Hospitalizations</h1>
			<p>Browse stays with department, bed, diagnosis, and KEN code.</p>
		</div>
	</div>
	<section class="panel overflow">
		<table>
			<thead>
			<tr>
				<th>ID</th>
				<th>Patient</th>
				<th>Department</th>
				<th>Bed</th>
				<th>Admission</th>
				<th>Discharge</th>
				<th>ICD-10</th>
				<th>KEN</th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($hospitalizations as $row): ?>
				<tr>
					<td><a href="?page=hospitalization&id=<?= h($row['id']) ?>"><?= h($row['id']) ?></a></td>
					<td><a href="?page=patient&id=<?= h($row['patient_amka']) ?>"><?= h($row['first_name'] . ' ' . $row['last_name']) ?></a></td>
					<td><?= h($row['department_name']) ?></td>
					<td><?= h($row['bed_number']) ?></td>
					<td><?= h($row['admission_date']) ?></td>
					<td><?= h($row['discharge_date'] ?? 'Open') ?></td>
					<td><?= h($row['admission_icd10']) ?></td>
					<td><?= h($row['ken_code']) ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>
	<?php
	render_footer();
}

function hospitalization_detail_page(): void
{
	$id = (int) param('id', 0);
	$hospitalization = fetch_one(
		'SELECT h.*, p.first_name, p.last_name, p.insurance, d.name AS department_name, b.bed_number,
				ac.description AS admission_description,
				dc.description AS discharge_description,
				k.description AS ken_description,
				k.base_cost,
				k.mean_los_days
		 FROM hospitalization h
		 JOIN patient p ON p.amka = h.patient_amka
		 JOIN department d ON d.id = h.department_id
		 JOIN bed b ON b.id = h.bed_id
		 JOIN icd10_code ac ON ac.code = h.admission_icd10
		 LEFT JOIN icd10_code dc ON dc.code = h.discharge_icd10
		 JOIN ken_code k ON k.code = h.ken_code
		 WHERE h.id = :id',
		[':id' => $id]
	);
	if ($hospitalization === null) {
		flash_set('error', 'Hospitalization not found.');
		redirect_to(['page' => 'hospitalizations']);
	}

	$procedures = fetch_all(
		'SELECT mp.id, mp.catalog_code, mp.start_datetime, mp.duration_minutes, mp.cost, mp.operating_room_id,
				pc.name AS procedure_name,
				CONCAT(sd.first_name, " ", sd.last_name) AS surgeon_name
		 FROM medical_procedure mp
		 JOIN procedure_catalog pc ON pc.code = mp.catalog_code
		 JOIN doctor d ON d.amka = mp.primary_surgeon_amka
		 JOIN staff sd ON sd.amka = d.amka
		 WHERE mp.hospitalization_id = :id
		 ORDER BY mp.start_datetime',
		[':id' => $id]
	);

	$prescriptions = fetch_all(
		'SELECT pr.id, pr.start_date, pr.end_date, pr.dosage, pr.frequency, dr.product_name
		 FROM prescription pr
		 JOIN drug dr ON dr.id = pr.drug_id
		 WHERE pr.hospitalization_id = :id
		 ORDER BY pr.start_date DESC',
		[':id' => $id]
	);

	$reviews = fetch_all(
		'SELECT id, patient_amka, nursing_care, cleanliness, food, overall_experience, review_date
		 FROM patient_review_hospitalization
		 WHERE hospitalization_id = :id',
		[':id' => $id]
	);

	render_header('hospitalization');
	?>
	<div class="section-head">
		<div>
			<h1>Hospitalization #<?= h($hospitalization['id']) ?></h1>
			<p><?= h($hospitalization['first_name'] . ' ' . $hospitalization['last_name']) ?> · <?= h($hospitalization['department_name']) ?> · <?= h($hospitalization['bed_number']) ?></p>
		</div>
		<a class="button secondary" href="?page=patient&id=<?= h($hospitalization['patient_amka']) ?>">Patient profile</a>
	</div>

	<div class="grid cols-3">
		<div class="card"><span class="muted">Admission</span><div><?= h($hospitalization['admission_date']) ?></div></div>
		<div class="card"><span class="muted">Discharge</span><div><?= h($hospitalization['discharge_date'] ?? 'Open') ?></div></div>
		<div class="card"><span class="muted">Insurance</span><div><?= h($hospitalization['insurance']) ?></div></div>
		<div class="card"><span class="muted">Admission diagnosis</span><div><?= h($hospitalization['admission_icd10']) ?> · <?= h($hospitalization['admission_description']) ?></div></div>
		<div class="card"><span class="muted">Discharge diagnosis</span><div><?= h(($hospitalization['discharge_icd10'] ?? 'n/a') . ' · ' . ($hospitalization['discharge_description'] ?? '')) ?></div></div>
		<div class="card"><span class="muted">KEN</span><div><?= h($hospitalization['ken_code']) ?> · <?= h($hospitalization['ken_description']) ?></div></div>
	</div>

	<div style="height: 18px"></div>

	<section class="panel">
		<h2>Costing context</h2>
		<div class="grid cols-3" style="margin-top: 14px;">
			<div class="card"><span class="muted">Base cost</span><div><?= h($hospitalization['base_cost']) ?></div></div>
			<div class="card"><span class="muted">Mean length of stay</span><div><?= h($hospitalization['mean_los_days']) ?></div></div>
			<div class="card"><span class="muted">Triage ID</span><div><?= h($hospitalization['triage_id'] ?? 'n/a') ?></div></div>
		</div>
	</section>

	<div style="height: 18px"></div>

	<section class="panel overflow">
		<div class="section-head">
			<div>
				<h2>Procedures</h2>
				<p>Joined to procedure catalog and surgeon.</p>
			</div>
		</div>
		<table>
			<thead>
			<tr>
				<th>ID</th>
				<th>Procedure</th>
				<th>Start</th>
				<th>Duration</th>
				<th>Cost</th>
				<th>Surgeon</th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($procedures as $row): ?>
				<tr>
					<td><?= h($row['id']) ?></td>
					<td><?= h($row['catalog_code'] . ' · ' . $row['procedure_name']) ?></td>
					<td><?= h($row['start_datetime']) ?></td>
					<td><?= h($row['duration_minutes']) ?></td>
					<td><?= h($row['cost']) ?></td>
					<td><?= h($row['surgeon_name']) ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>

	<div style="height: 18px"></div>

	<section class="panel overflow">
		<div class="section-head">
			<div>
				<h2>Prescriptions</h2>
				<p>Direct drug linkage from the hospitalization record.</p>
			</div>
		</div>
		<table>
			<thead>
			<tr>
				<th>ID</th>
				<th>Drug</th>
				<th>Start</th>
				<th>End</th>
				<th>Dosage</th>
				<th>Frequency</th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($prescriptions as $row): ?>
				<tr>
					<td><?= h($row['id']) ?></td>
					<td><?= h($row['product_name']) ?></td>
					<td><?= h($row['start_date']) ?></td>
					<td><?= h($row['end_date'] ?? 'Open') ?></td>
					<td><?= h($row['dosage']) ?></td>
					<td><?= h($row['frequency']) ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>

	<div style="height: 18px"></div>

	<section class="panel overflow">
		<div class="section-head">
			<div>
				<h2>Hospitalization reviews</h2>
				<p>Patient feedback captured after the stay.</p>
			</div>
		</div>
		<table>
			<thead>
			<tr>
				<th>ID</th>
				<th>Patient</th>
				<th>Nursing</th>
				<th>Cleanliness</th>
				<th>Food</th>
				<th>Overall</th>
				<th>Date</th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($reviews as $row): ?>
				<tr>
					<td><?= h($row['id']) ?></td>
					<td><?= h($row['patient_amka']) ?></td>
					<td><?= h($row['nursing_care']) ?></td>
					<td><?= h($row['cleanliness']) ?></td>
					<td><?= h($row['food']) ?></td>
					<td><?= h($row['overall_experience']) ?></td>
					<td><?= h($row['review_date']) ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>
	<?php
	render_footer();
}

function drugs_page(): void
{
	$q = trim((string) param('q', ''));
	$limit = safe_limit_value(param('limit', 25));
	$params = [];
	$where = '';
	if ($q !== '') {
		$where = 'WHERE d.product_name LIKE :drug_name_query OR d.marketing_authorisation_holder LIKE :holder_query OR d.product_authorisation_country LIKE :country_query';
		$params = [
			':drug_name_query' => '%' . $q . '%',
			':holder_query' => '%' . $q . '%',
			':country_query' => '%' . $q . '%',
		];
	}

	$drugs = fetch_all(
		'SELECT d.id, d.product_name, d.route_of_administration, d.product_authorisation_country,
				COUNT(DISTINCT das.substance_id) AS substance_count
		 FROM drug d
		 LEFT JOIN drug_active_substance das ON das.drug_id = d.id
		 ' . $where . '
		 GROUP BY d.id
		 ORDER BY d.product_name
		 LIMIT ' . (int) $limit,
		$params
	);

	render_header('drugs');
	?>
	<div class="section-head">
		<div>
			<h1>Drugs</h1>
			<p>EMA Article 57 product data and active substance links.</p>
		</div>
	</div>

	<div class="panel">
		<form method="get" class="form-grid">
			<input type="hidden" name="page" value="drugs">
			<div>
				<label for="q">Search</label>
				<input id="q" name="q" value="<?= h($q) ?>" placeholder="product, holder, or country">
			</div>
			<div>
				<label for="limit">Rows</label>
				<select id="limit" name="limit">
					<?php foreach ([10, 25, 50, 100] as $option): ?>
						<option value="<?= h($option) ?>" <?= selected((string) $option, (string) $limit) ?>><?= h($option) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div class="full actions">
				<input type="submit" value="Apply filters">
				<a class="button secondary" href="?page=drugs">Reset</a>
			</div>
		</form>
	</div>

	<div style="height: 18px"></div>
	<section class="panel overflow">
		<table>
			<thead>
			<tr>
				<th>Product</th>
				<th>Route</th>
				<th>Country</th>
				<th>Substances</th>
				<th></th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($drugs as $row): ?>
				<tr class="row-selectable" tabindex="0" data-row-select="1" data-href="?page=drug&id=<?= h($row['id']) ?>">
					<td><?= h($row['product_name']) ?></td>
					<td><?= h($row['route_of_administration'] ?? 'n/a') ?></td>
					<td><?= h($row['product_authorisation_country'] ?? 'n/a') ?></td>
					<td><?= h($row['substance_count']) ?></td>
					<td><a class="button secondary" href="?page=drug&id=<?= h($row['id']) ?>">Open</a></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>
	<?php
	render_footer();
}

function drug_detail_page(): void
{
	$id = (int) param('id', 0);
	$drug = fetch_one('SELECT * FROM drug WHERE id = :id', [':id' => $id]);
	if ($drug === null) {
		flash_set('error', 'Drug not found.');
		redirect_to(['page' => 'drugs']);
	}

	$substances = fetch_all(
		'SELECT s.id, s.name
		 FROM active_substance s
		 JOIN drug_active_substance das ON das.substance_id = s.id
		 WHERE das.drug_id = :id
		 ORDER BY s.name',
		[':id' => $id]
	);

	$prescriptions = fetch_all(
		'SELECT pr.id, pr.start_date, pr.end_date, p.first_name, p.last_name, pr.dosage, pr.frequency
		 FROM prescription pr
		 JOIN patient p ON p.amka = pr.patient_amka
		 WHERE pr.drug_id = :id
		 ORDER BY pr.start_date DESC
		 LIMIT 20',
		[':id' => $id]
	);

	render_header('drug');
	?>
	<div class="section-head">
		<div>
			<h1><?= h($drug['product_name']) ?></h1>
			<p><?= h($drug['marketing_authorisation_holder'] ?? 'n/a') ?> · <?= h($drug['product_authorisation_country'] ?? 'n/a') ?></p>
		</div>
	</div>

	<div class="grid cols-2">
		<section class="panel">
			<h2>Drug metadata</h2>
			<div class="grid cols-2" style="margin-top: 14px;">
				<div class="card"><span class="muted">Route</span><div><?= h($drug['route_of_administration'] ?? 'n/a') ?></div></div>
				<div class="card"><span class="muted">Country</span><div><?= h($drug['product_authorisation_country'] ?? 'n/a') ?></div></div>
				<div class="card full"><span class="muted">PV contact</span><div><?= h($drug['pharmacovigilance_email'] ?? 'n/a') ?> · <?= h($drug['pharmacovigilance_phone'] ?? 'n/a') ?></div></div>
				<div class="card full"><span class="muted">Master file</span><div><?= h($drug['pharmacovigilance_master_file_location'] ?? 'n/a') ?></div></div>
			</div>
		</section>

		<section class="panel">
			<h2>Active substances</h2>
			<div class="stack" style="margin-top: 14px;">
				<?php foreach ($substances as $substance): ?>
					<div class="badge ok"><?= h($substance['name']) ?></div>
				<?php endforeach; ?>
				<?php if ($substances === []): ?>
					<p>No substance mapping found.</p>
				<?php endif; ?>
			</div>
		</section>
	</div>

	<div style="height: 18px"></div>

	<section class="panel overflow">
		<div class="section-head">
			<div>
				<h2>Prescriptions using this drug</h2>
				<p>Recent patients and dosage instructions.</p>
			</div>
		</div>
		<table>
			<thead>
			<tr>
				<th>ID</th>
				<th>Patient</th>
				<th>Start</th>
				<th>End</th>
				<th>Dosage</th>
				<th>Frequency</th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($prescriptions as $row): ?>
				<tr>
					<td><?= h($row['id']) ?></td>
					<td><?= h($row['first_name'] . ' ' . $row['last_name']) ?></td>
					<td><?= h($row['start_date']) ?></td>
					<td><?= h($row['end_date'] ?? 'Open') ?></td>
					<td><?= h($row['dosage']) ?></td>
					<td><?= h($row['frequency']) ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>
	<?php
	render_footer();
}

function staff_page(): void
{
	$q = trim((string) param('q', ''));
	$limit = safe_limit_value(param('limit', 25));
	$params = [];
	$where = '';
	if ($q !== '') {
		$where = 'WHERE s.amka LIKE :amka_query OR s.first_name LIKE :first_name_query OR s.last_name LIKE :last_name_query OR s.email LIKE :email_query OR d.specialty LIKE :specialty_query OR n.rank LIKE :nurse_rank_query OR a.role LIKE :role_query';
		$params = [
			':amka_query' => '%' . $q . '%',
			':first_name_query' => '%' . $q . '%',
			':last_name_query' => '%' . $q . '%',
			':email_query' => '%' . $q . '%',
			':specialty_query' => '%' . $q . '%',
			':nurse_rank_query' => '%' . $q . '%',
			':role_query' => '%' . $q . '%',
		];
	}

	$staff = fetch_all(
		'SELECT s.amka, s.first_name, s.last_name, s.staff_type, s.email, s.phone, s.hire_date,
				d.specialty, d.rank AS doctor_rank,
				n.rank AS nurse_rank, n.department_id AS nurse_department,
				a.role AS admin_role, a.department_id AS admin_department
		 FROM staff s
		 LEFT JOIN doctor d ON d.amka = s.amka
		 LEFT JOIN nurse n ON n.amka = s.amka
		 LEFT JOIN admin_staff a ON a.amka = s.amka
		 ' . $where . '
		 ORDER BY s.last_name, s.first_name
		 LIMIT ' . (int) $limit,
		$params
	);

	render_header('staff');
	?>
	<div class="section-head">
		<div>
			<h1>Staff</h1>
			<p>Unified view across doctors, nurses, and administrative staff.</p>
		</div>
	</div>

	<div class="panel">
		<form method="get" class="form-grid">
			<input type="hidden" name="page" value="staff">
			<div>
				<label for="q">Search</label>
				<input id="q" name="q" value="<?= h($q) ?>" placeholder="AMKA, name, email, specialty, role">
			</div>
			<div>
				<label for="limit">Rows</label>
				<select id="limit" name="limit">
					<?php foreach ([10, 25, 50, 100] as $option): ?>
						<option value="<?= h($option) ?>" <?= selected((string) $option, (string) $limit) ?>><?= h($option) ?></option>
					<?php endforeach; ?>
				</select>
			</div>
			<div class="full actions">
				<input type="submit" value="Apply filters">
				<a class="button secondary" href="?page=staff">Reset</a>
			</div>
		</form>
	</div>

	<div style="height: 18px"></div>
	<section class="panel overflow">
		<table>
			<thead>
			<tr>
				<th>AMKA</th>
				<th>Name</th>
				<th>Type</th>
				<th>Role / specialty</th>
				<th>Contact</th>
			</tr>
			</thead>
			<tbody>
			<?php foreach ($staff as $row): ?>
				<tr class="row-selectable" tabindex="0" data-row-select="1">
					<td><?= h($row['amka']) ?></td>
					<td><?= h($row['last_name'] . ', ' . $row['first_name']) ?></td>
					<td><?= h($row['staff_type']) ?></td>
					<td><?= h($row['specialty'] ?? $row['doctor_rank'] ?? $row['nurse_rank'] ?? $row['admin_role'] ?? 'n/a') ?></td>
					<td><?= h($row['email'] ?? 'n/a') ?><br><?= h($row['phone'] ?? 'n/a') ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
	</section>
	<?php
	render_footer();
}

function search_page(): void
{
	$q = trim((string) param('q', ''));
	$patients = $departments = $drugs = [];
	if ($q !== '') {
		$like = '%' . $q . '%';
		$patients = fetch_all(
			'SELECT amka, first_name, last_name FROM patient WHERE amka LIKE :patient_amka_query OR first_name LIKE :patient_first_name_query OR last_name LIKE :patient_last_name_query ORDER BY last_name, first_name LIMIT 10',
			[
				':patient_amka_query' => $like,
				':patient_first_name_query' => $like,
				':patient_last_name_query' => $like,
			]
		);
		$departments = fetch_all(
			'SELECT id, name FROM department WHERE name LIKE :department_name_query OR description LIKE :department_description_query ORDER BY name LIMIT 10',
			[
				':department_name_query' => $like,
				':department_description_query' => $like,
			]
		);
		$drugs = fetch_all(
			'SELECT id, product_name FROM drug WHERE product_name LIKE :drug_name_query ORDER BY product_name LIMIT 10',
			[':drug_name_query' => $like]
		);
	}

	render_header('search');
	?>
	<div class="section-head">
		<div>
			<h1>Search</h1>
			<p>Quick lookup across the main tables that users are likely to navigate first.</p>
		</div>
	</div>

	<section class="panel">
		<form method="get" class="form-grid">
			<input type="hidden" name="page" value="search">
			<div class="full">
				<label for="q">Search term</label>
				<input id="q" name="q" value="<?= h($q) ?>" placeholder="name, department, or product">
			</div>
			<div class="full actions">
				<input type="submit" value="Search">
			</div>
		</form>
	</section>

	<?php if ($q !== ''): ?>
		<div style="height: 18px"></div>
		<div class="grid cols-3">
			<section class="panel overflow">
				<h2>Patients</h2>
				<table>
					<tbody>
					<?php foreach ($patients as $row): ?>
						<tr><td><a href="?page=patient&id=<?= h($row['amka']) ?>"><?= h($row['last_name'] . ', ' . $row['first_name']) ?></a></td></tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			</section>
			<section class="panel overflow">
				<h2>Departments</h2>
				<table>
					<tbody>
					<?php foreach ($departments as $row): ?>
						<tr><td><a href="?page=department&id=<?= h($row['id']) ?>"><?= h($row['name']) ?></a></td></tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			</section>
			<section class="panel overflow">
				<h2>Drugs</h2>
				<table>
					<tbody>
					<?php foreach ($drugs as $row): ?>
						<tr><td><a href="?page=drug&id=<?= h($row['id']) ?>"><?= h($row['product_name']) ?></a></td></tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			</section>
		</div>
	<?php endif; ?>
	<?php
	render_footer();
}

function handle_routing(string $page): void
{
	match ($page) {
		'patients' => patient_list_page(),
		'patient' => patient_detail_page(),
		'patient-new' => patient_new_page(),
		'patient-edit' => patient_edit_page(),
		'patient-save' => patient_save(),
		'patient-delete' => patient_delete(),
		'patient-allergy-add' => patient_allergy_add(),
		'departments' => department_list_page(),
		'department' => department_detail_page(),
		'department-new' => department_new_page(),
		'department-edit' => department_edit_page(),
		'department-save' => department_save(),
		'hospitalizations' => hospitalization_list_page(),
		'hospitalization' => hospitalization_detail_page(),
		'drugs' => drugs_page(),
		'drug' => drug_detail_page(),
		'staff' => staff_page(),
		'search' => search_page(),
		default => dashboard_page(),
	};
}

if (pdo() instanceof PDO) {
	$page = (string) param('page', 'dashboard');
	handle_routing($page);
} else {
	render_header('dashboard');
	?>
	<section class="panel">
		<h1>Database connection unavailable</h1>
		<p>The web UI is installed, but it cannot reach MariaDB yet. Check the container name, credentials, and whether the schema has been created.</p>
	</section>
	<?php
	render_footer();
}
?>
