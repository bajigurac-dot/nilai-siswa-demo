"""
app_demo.py — Versi DEMO (data fiktif, tidak ada data asli)
Jalankan: python app_demo.py
Akses   : http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from functools import wraps
import pandas as pd
import sqlite3
import io
import os
import random
from datetime import date, timedelta
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = 'demo-nilai-siswa-2025'
DB = 'demo.db'

# ── Konstanta ────────────────────────────────────────────────────────────────

JENIS_NILAI = ['PTS', 'Latihan Harian', 'UTS', 'UAS', 'Tugas', 'Praktik']

DEMO_SISWA = {
    'X': [
        'AHMAD FAUZI', 'BUDI SANTOSO', 'CITRA DEWI', 'DENI RAMADAN', 'EKA PUTRI',
        'FAJAR NUGROHO', 'GITA LESTARI', 'HENDRA WIJAYA', 'INDAH PERMATA', 'JOKO SUSILO',
        'KURNIA SARI', 'LUTHFI HAKIM', 'MAYA ANGGRAINI', 'NANDA PRATAMA', 'OKI SETIAWAN',
    ],
    'XI': [
        'PUTRI RAHAYU', 'QORI AMALIA', 'RIZKY FIRMANSYAH', 'SARI WULANDARI', 'TAUFIK HIDAYAT',
        'UMAR FARUQ', 'VINA MELATI', 'WAHYU SAPUTRA', 'XENA APRILIA', 'YUSUF MAULANA',
        'ZARA AULIA', 'ANDI SUPRIADI', 'BELLA SAFITRI', 'CAHYO PRABOWO', 'DINA FITRIANI',
    ],
    'XII': [
        'EDI KUNCORO', 'FITRI HANDAYANI', 'GILANG RAMADHAN', 'HANA NOVITA', 'IRFAN BAKRI',
        'JULIA SARI', 'KEVIN ALEXANDER', 'LAILA MAGHFIRA', 'MOCH ALFARIZI', 'NITA AMELIA',
        'OSCAR PRANATA', 'PRAMESTI DEWI', 'RAKA ADITYA', 'SINTA PERMATA', 'TOMMY SURYA',
    ],
}

# ── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS absensi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL, kelas TEXT NOT NULL, tanggal TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Hadir','Sakit','Izin','Alpha')),
            keterangan TEXT, UNIQUE(nama, kelas, tanggal)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE, password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('guru','siswa')),
            nama TEXT NOT NULL, kelas TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS nilai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL, kelas TEXT NOT NULL,
            jenis TEXT NOT NULL, nilai REAL NOT NULL,
            tanggal TEXT NOT NULL, keterangan TEXT,
            UNIQUE(nama, kelas, jenis, tanggal)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS siswa_tambahan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL, kelas TEXT NOT NULL, UNIQUE(nama, kelas)
        )''')

def seed_demo():
    """Isi database demo dengan data fiktif jika masih kosong."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] > 0:
        conn.close()
        return  # sudah di-seed

    random.seed(42)

    # ── Akun guru ──
    conn.execute('INSERT INTO users (username,password,role,nama,kelas) VALUES (?,?,?,?,?)',
                 ('guru', 'guru123', 'guru', 'Bpk. Demo Guru', None))

    # ── Akun siswa ──
    for kelas, daftar in DEMO_SISWA.items():
        for nama in daftar:
            first = nama.split()[0].lower()
            existing = conn.execute('SELECT COUNT(*) FROM users WHERE username=?', (first,)).fetchone()[0]
            username = first if existing == 0 else f"{first}{kelas.lower()}"
            base, counter = username, 2
            while conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone():
                username = f"{base}{counter}"; counter += 1
            conn.execute(
                'INSERT OR IGNORE INTO users (username,password,role,nama,kelas) VALUES (?,?,?,?,?)',
                (username, 'siswa123', 'siswa', nama, kelas)
            )

    # ── Seed nilai PTS ──
    pts_date = '2025-06-15'
    for kelas, daftar in DEMO_SISWA.items():
        base_score = {'X': 75, 'XI': 78, 'XII': 80}[kelas]
        for nama in daftar:
            nilai = min(100, max(55, int(random.gauss(base_score, 10))))
            conn.execute(
                'INSERT OR IGNORE INTO nilai (nama,kelas,jenis,nilai,tanggal,keterangan) VALUES (?,?,?,?,?,?)',
                (nama, kelas, 'PTS', nilai, pts_date, 'PTS Semester 1')
            )

    # ── Seed nilai lainnya ──
    extra_jenis = [
        ('Latihan Harian', '2025-07-01', 'Latihan Bab 1'),
        ('Tugas',          '2025-07-08', 'Tugas Kelompok'),
        ('Praktik',        '2025-07-10', 'Praktik Komputer'),
    ]
    for kelas, daftar in DEMO_SISWA.items():
        for jenis, tgl, ket in extra_jenis:
            for nama in daftar:
                nilai = min(100, max(60, int(random.gauss(82, 8))))
                conn.execute(
                    'INSERT OR IGNORE INTO nilai (nama,kelas,jenis,nilai,tanggal,keterangan) VALUES (?,?,?,?,?,?)',
                    (nama, kelas, jenis, nilai, tgl, ket)
                )

    # ── Seed absensi (7 hari terakhir) ──
    statuses = ['Hadir', 'Hadir', 'Hadir', 'Hadir', 'Sakit', 'Izin', 'Alpha']
    today = date.today()
    for delta in range(7, 0, -1):
        tgl = (today - timedelta(days=delta)).isoformat()
        for kelas, daftar in DEMO_SISWA.items():
            for nama in daftar:
                status = random.choice(statuses)
                ket = 'Demam' if status == 'Sakit' else ('Keperluan keluarga' if status == 'Izin' else '')
                conn.execute(
                    'INSERT OR IGNORE INTO absensi (nama,kelas,tanggal,status,keterangan) VALUES (?,?,?,?,?)',
                    (nama, kelas, tgl, status, ket)
                )

    conn.commit()
    conn.close()

# ── Auth decorators ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def guru_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'guru':
            flash('Akses ditolak. Hanya guru yang dapat melakukan ini.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ── Helpers ──────────────────────────────────────────────────────────────────

def grade(n):
    if n >= 90: return 'A'
    elif n >= 80: return 'B'
    elif n >= 70: return 'C'
    elif n >= 60: return 'D'
    else: return 'E'

def build_class_from_db(kelas, jenis='PTS', tanggal=None):
    q = 'SELECT * FROM nilai WHERE kelas=? AND jenis=?'
    p = [kelas, jenis]
    if tanggal:
        q += ' AND tanggal=?'; p.append(tanggal)
    else:
        q += ''' AND tanggal=(
            SELECT MAX(tanggal) FROM nilai n2
            WHERE n2.nama=nilai.nama AND n2.kelas=nilai.kelas AND n2.jenis=nilai.jenis
        )'''
    rows = get_db().execute(q, p).fetchall()
    if not rows:
        return None
    df = pd.DataFrame([dict(r) for r in rows])
    df = df.sort_values('nilai', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1
    df['Grade'] = df['nilai'].apply(grade)
    grade_dist = df['Grade'].value_counts().to_dict()
    for g in ['A', 'B', 'C', 'D', 'E']:
        grade_dist.setdefault(g, 0)
    return {
        'students': [{'Rank': int(r['Rank']), 'Nama': r['nama'], 'Nilai': r['nilai'],
                      'Grade': r['Grade'], 'Waktu': r['tanggal']} for _, r in df.iterrows()],
        'student_count': len(df),
        'class_average': round(df['nilai'].mean(), 2),
        'max_score': int(df['nilai'].max()),
        'min_score': int(df['nilai'].min()),
        'highest': df.iloc[0]['nama'],
        'lowest': df.iloc[-1]['nama'],
        'grade_dist': grade_dist,
        'grade_values': [grade_dist.get(g, 0) for g in ['A', 'B', 'C', 'D', 'E']],
    }

def load_all():
    classes, errors = {}, {}
    for kelas in ['X', 'XI', 'XII']:
        data = build_class_from_db(kelas, 'PTS')
        if data:
            classes[kelas] = data
        else:
            errors[kelas] = 'Belum ada data PTS'
    summary = None
    if classes:
        total_siswa = sum(c['student_count'] for c in classes.values())
        all_avg = [c['class_average'] for c in classes.values()]
        summary = {
            'total_siswa': total_siswa,
            'rata_rata_gabungan': round(sum(all_avg) / len(all_avg), 2),
            'kelas_terbaik': max(classes, key=lambda k: classes[k]['class_average']),
            'per_kelas': {k: {'avg': v['class_average'], 'count': v['student_count']} for k, v in classes.items()},
            'avg_values': [classes[k]['class_average'] if k in classes else 0 for k in ['X', 'XI', 'XII']],
        }
    return classes, summary, errors

def get_students_by_class():
    students = {}
    for kelas, daftar in DEMO_SISWA.items():
        students[kelas] = sorted(daftar)
    tambahan = get_db().execute('SELECT nama, kelas FROM siswa_tambahan').fetchall()
    for row in tambahan:
        k = row['kelas']
        if k not in students:
            students[k] = []
        if row['nama'] not in students[k]:
            students[k] = sorted(students[k] + [row['nama']])
    return students

def get_nilai_db(kelas=None, jenis=None, tanggal=None, nama=None):
    db = get_db()
    q = 'SELECT * FROM nilai WHERE 1=1'
    p = []
    if kelas:   q += ' AND kelas=?';   p.append(kelas)
    if jenis:   q += ' AND jenis=?';   p.append(jenis)
    if tanggal: q += ' AND tanggal=?'; p.append(tanggal)
    if nama:    q += ' AND nama=?';    p.append(nama)
    q += ' ORDER BY tanggal DESC, kelas, nama'
    return db.execute(q, p).fetchall()

def get_jenis_tersedia():
    rows = get_db().execute('SELECT DISTINCT jenis FROM nilai ORDER BY jenis').fetchall()
    return [r['jenis'] for r in rows]

def get_absensi_rekap(kelas=None, tanggal=None, nama=None):
    db = get_db()
    q = 'SELECT * FROM absensi WHERE 1=1'
    p = []
    if kelas:   q += ' AND kelas=?';   p.append(kelas)
    if tanggal: q += ' AND tanggal=?'; p.append(tanggal)
    if nama:    q += ' AND nama=?';    p.append(nama)
    q += ' ORDER BY tanggal DESC, kelas, nama'
    return db.execute(q, p).fetchall()

def get_absensi_summary(kelas=None, nama=None):
    db = get_db()
    q = '''SELECT nama,
        SUM(CASE WHEN status='Hadir' THEN 1 ELSE 0 END) as hadir,
        SUM(CASE WHEN status='Sakit' THEN 1 ELSE 0 END) as sakit,
        SUM(CASE WHEN status='Izin'  THEN 1 ELSE 0 END) as izin,
        SUM(CASE WHEN status='Alpha' THEN 1 ELSE 0 END) as alpha,
        COUNT(*) as total FROM absensi WHERE 1=1'''
    p = []
    if kelas: q += ' AND kelas=?'; p.append(kelas)
    if nama:  q += ' AND nama=?';  p.append(nama)
    q += ' GROUP BY nama ORDER BY nama'
    return db.execute(q, p).fetchall()

# ── Auth routes ──────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    # Ambil beberapa akun siswa demo untuk ditampilkan di halaman login
    demo_accounts = get_db().execute(
        "SELECT username, kelas FROM users WHERE role='siswa' ORDER BY kelas, username LIMIT 6"
    ).fetchall()
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = get_db().execute(
            'SELECT * FROM users WHERE username=? AND password=?', (username, password)
        ).fetchone()
        if user:
            session.update({'user_id': user['id'], 'username': user['username'],
                            'role': user['role'], 'nama': user['nama'], 'kelas': user['kelas']})
            return redirect(url_for('index'))
        flash('Username atau password salah!', 'danger')
    return render_template('login.html', is_demo=True, demo_accounts=demo_accounts)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Main dashboard ───────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    if session.get('role') == 'siswa':
        nama_siswa  = session.get('nama')
        kelas_siswa = session.get('kelas')
        # Ambil nilai PTS dari DB
        nilai_pts = None
        pts_rows = get_db().execute(
            "SELECT * FROM nilai WHERE nama=? AND kelas=? AND jenis='PTS' ORDER BY tanggal DESC LIMIT 1",
            (nama_siswa, kelas_siswa)
        ).fetchone()
        if pts_rows:
            # Hitung rank
            all_pts = get_db().execute(
                "SELECT nama, nilai FROM nilai WHERE kelas=? AND jenis='PTS' ORDER BY nilai DESC",
                (kelas_siswa,)
            ).fetchall()
            rank = next((i+1 for i, r in enumerate(all_pts) if r['nama'] == nama_siswa), None)
            nilai_pts = {
                'Nama': nama_siswa, 'Nilai': pts_rows['nilai'],
                'Grade': grade(pts_rows['nilai']), 'Rank': rank,
                'total_siswa': len(all_pts), 'Waktu': pts_rows['tanggal'],
            }
        nilai_db      = get_nilai_db(nama=nama_siswa)
        absensi_siswa = get_absensi_rekap(nama=nama_siswa)
        summary_siswa = get_absensi_summary(nama=nama_siswa)
        return render_template('siswa.html',
            nilai_pts=nilai_pts, nilai_db=nilai_db,
            absensi=absensi_siswa,
            summary=summary_siswa[0] if summary_siswa else None,
            nama=nama_siswa, kelas=kelas_siswa
        )
    return render_template('index.html', **_guru_context())

def _guru_context(extra=None):
    classes, summary, errors = load_all()
    today = date.today().isoformat()
    students_by_class = get_students_by_class()
    jenis_tersedia = get_jenis_tersedia()
    nilai_list = get_nilai_db()
    ctx = dict(
        classes=classes, summary=summary, errors=errors,
        students_by_class=students_by_class,
        today=today,
        absensi_hari_ini={row['nama']: dict(row) for row in get_absensi_rekap(tanggal=today)},
        absensi_summary={k: get_absensi_summary(kelas=k) for k in ['X', 'XI', 'XII']},
        absensi_detail={k: get_absensi_rekap(kelas=k) for k in ['X', 'XI', 'XII']},
        users=get_db().execute('SELECT id,username,role,nama,kelas FROM users ORDER BY role,nama').fetchall(),
        siswa_tambahan=get_db().execute('SELECT * FROM siswa_tambahan ORDER BY kelas, nama').fetchall(),
        jenis_nilai=JENIS_NILAI,
        jenis_tersedia=jenis_tersedia,
        nilai_list=nilai_list,
        active_tab=None,
        admin_sql=None, admin_result=[], admin_columns=[], admin_error=None,
        is_demo=True,
    )
    if extra:
        ctx.update(extra)
    return ctx

# ── Nilai routes ─────────────────────────────────────────────────────────────

@app.route('/nilai/simpan', methods=['POST'])
@guru_required
def simpan_nilai():
    kelas   = request.form['kelas']
    jenis   = request.form['jenis_input'] if request.form['jenis'] == '__baru__' else request.form['jenis']
    tanggal = request.form['tanggal']
    names   = request.form.getlist('nama[]')
    scores  = request.form.getlist('nilai[]')
    ket     = request.form.get('keterangan', '')
    saved   = 0
    with get_db() as db:
        for nama, nilai in zip(names, scores):
            if nama and nilai:
                try:
                    db.execute('''INSERT INTO nilai (nama,kelas,jenis,nilai,tanggal,keterangan)
                        VALUES (?,?,?,?,?,?)
                        ON CONFLICT(nama,kelas,jenis,tanggal) DO UPDATE SET
                            nilai=excluded.nilai, keterangan=excluded.keterangan
                    ''', (nama.strip(), kelas, jenis.strip(), float(nilai), tanggal, ket))
                    saved += 1
                except ValueError:
                    pass
    flash(f'{saved} nilai {jenis} Kelas {kelas} tanggal {tanggal} berhasil disimpan!', 'success')
    return redirect(url_for('index') + '#tabNilaiDB')

@app.route('/nilai/hapus/<int:id>')
@guru_required
def hapus_nilai(id):
    with get_db() as db:
        db.execute('DELETE FROM nilai WHERE id=?', (id,))
    flash('Data nilai berhasil dihapus!', 'danger')
    return redirect(url_for('index') + '#tabNilaiDB')

@app.route('/nilai/hapus-batch', methods=['POST'])
@guru_required
def hapus_nilai_batch():
    kelas   = request.form['kelas']
    jenis   = request.form['jenis']
    tanggal = request.form['tanggal']
    with get_db() as db:
        cur = db.execute('DELETE FROM nilai WHERE kelas=? AND jenis=? AND tanggal=?', (kelas, jenis, tanggal))
    flash(f'{cur.rowcount} data nilai {jenis} Kelas {kelas} tanggal {tanggal} dihapus!', 'danger')
    return redirect(url_for('index') + '#tabNilaiDB')

# ── Absensi routes ───────────────────────────────────────────────────────────

@app.route('/absensi/simpan', methods=['POST'])
@guru_required
def simpan_absensi():
    kelas   = request.form['kelas']
    tanggal = request.form['tanggal']
    names   = request.form.getlist('nama[]')
    statuses    = request.form.getlist('status[]')
    keterangans = request.form.getlist('keterangan[]')
    with get_db() as db:
        for nama, status, ket in zip(names, statuses, keterangans):
            if nama and status:
                db.execute('''INSERT INTO absensi (nama,kelas,tanggal,status,keterangan) VALUES (?,?,?,?,?)
                    ON CONFLICT(nama,kelas,tanggal) DO UPDATE SET
                        status=excluded.status, keterangan=excluded.keterangan
                ''', (nama.strip(), kelas, tanggal, status, ket))
    flash(f'Absensi Kelas {kelas} tanggal {tanggal} berhasil disimpan!', 'success')
    return redirect(url_for('index'))

@app.route('/absensi/edit/<int:id>', methods=['POST'])
@guru_required
def edit_absensi(id):
    with get_db() as db:
        db.execute('UPDATE absensi SET status=?, keterangan=? WHERE id=?',
                   (request.form['status'], request.form.get('keterangan', ''), id))
    flash('Data absensi berhasil diperbarui!', 'success')
    return redirect(url_for('index'))

@app.route('/absensi/hapus/<int:id>')
@guru_required
def hapus_absensi(id):
    with get_db() as db:
        db.execute('DELETE FROM absensi WHERE id=?', (id,))
    flash('Data absensi berhasil dihapus!', 'danger')
    return redirect(url_for('index'))

# ── Siswa tambahan ───────────────────────────────────────────────────────────

@app.route('/siswa/tambah', methods=['POST'])
@guru_required
def tambah_siswa():
    nama  = request.form['nama'].strip().upper()
    kelas = request.form['kelas']
    try:
        with get_db() as db:
            db.execute('INSERT INTO siswa_tambahan (nama, kelas) VALUES (?, ?)', (nama, kelas))
        flash(f'Siswa "{nama}" Kelas {kelas} berhasil ditambahkan!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Siswa "{nama}" di Kelas {kelas} sudah ada!', 'danger')
    return redirect(url_for('index'))

@app.route('/siswa/hapus/<int:id>')
@guru_required
def hapus_siswa(id):
    with get_db() as db:
        db.execute('DELETE FROM siswa_tambahan WHERE id=?', (id,))
    flash('Siswa berhasil dihapus!', 'danger')
    return redirect(url_for('index'))

# ── User management ──────────────────────────────────────────────────────────

@app.route('/users/tambah', methods=['POST'])
@guru_required
def tambah_user():
    username = request.form['username'].strip()
    password = request.form['password']
    role     = request.form['role']
    nama     = request.form['nama'].strip().upper()
    kelas    = request.form.get('kelas') or None
    try:
        with get_db() as db:
            db.execute('INSERT INTO users (username,password,role,nama,kelas) VALUES (?,?,?,?,?)',
                       (username, password, role, nama, kelas))
        flash(f'Akun "{username}" berhasil ditambahkan!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Username "{username}" sudah digunakan!', 'danger')
    return redirect(url_for('index'))

@app.route('/users/hapus/<int:id>')
@guru_required
def hapus_user(id):
    if id == session.get('user_id'):
        flash('Tidak bisa menghapus akun sendiri!', 'danger')
        return redirect(url_for('index'))
    with get_db() as db:
        db.execute('DELETE FROM users WHERE id=?', (id,))
    flash('Akun berhasil dihapus!', 'danger')
    return redirect(url_for('index'))

@app.route('/users/reset-password/<int:id>', methods=['POST'])
@guru_required
def reset_password(id):
    with get_db() as db:
        db.execute('UPDATE users SET password=? WHERE id=?', (request.form['new_password'], id))
    flash('Password berhasil direset!', 'success')
    return redirect(url_for('index'))

# ── Admin query (READ-ONLY di demo) ──────────────────────────────────────────

@app.route('/admin/query', methods=['POST'])
@guru_required
def admin_query():
    sql = request.form.get('sql', '').strip()
    result, columns, error = [], [], None
    if sql:
        # Blokir query yang bisa merusak data demo (opsional: bisa dihapus jika mau bebas)
        sql_upper = sql.upper().lstrip()
        blocked = any(sql_upper.startswith(kw) for kw in ['DROP', 'TRUNCATE', 'ALTER', 'PRAGMA'])
        if blocked:
            error = '⚠️ Mode demo: perintah DROP/ALTER/TRUNCATE dinonaktifkan.'
        else:
            try:
                db = get_db()
                cur = db.execute(sql)
                if cur.description:
                    columns = [d[0] for d in cur.description]
                    result  = [list(r) for r in cur.fetchall()]
                else:
                    db.commit()
                    result  = [[f'{cur.rowcount} baris terpengaruh']]
                    columns = ['Info']
            except Exception as e:
                error = str(e)
    return render_template('index.html', **_guru_context({
        'admin_sql': sql, 'admin_result': result,
        'admin_columns': columns, 'admin_error': error,
        'active_tab': 'admin', 'is_demo': True,
    }))

# ── Export ───────────────────────────────────────────────────────────────────

@app.route('/export/nilai')
@guru_required
def export_nilai():
    classes, _, _ = load_all()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        for kelas, data in classes.items():
            df = pd.DataFrame([{'Rank': s['Rank'], 'Nama': s['Nama'],
                'Nilai': s['Nilai'], 'Grade': s['Grade'], 'Waktu': s['Waktu']}
                for s in data['students']])
            df.to_excel(writer, sheet_name=f'PTS Kelas {kelas}', index=False)
            ws = writer.sheets[f'PTS Kelas {kelas}']
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or '')) for c in col) + 4
        for row in get_db().execute('SELECT DISTINCT kelas, jenis FROM nilai ORDER BY kelas, jenis').fetchall():
            rows = get_nilai_db(kelas=row['kelas'], jenis=row['jenis'])
            if rows:
                sheet = f"{row['jenis']} {row['kelas']}"[:31]
                df = pd.DataFrame([{'Tanggal': r['tanggal'], 'Nama': r['nama'],
                    'Nilai': r['nilai'], 'Keterangan': r['keterangan'] or ''} for r in rows])
                df.to_excel(writer, sheet_name=sheet, index=False)
                ws = writer.sheets[sheet]
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or '')) for c in col) + 4
    buf.seek(0)
    return send_file(buf, as_attachment=True,
        download_name=f'Demo_Nilai_{date.today()}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export/absensi')
@guru_required
def export_absensi():
    kelas_filter = request.args.get('kelas')
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        for kelas in ([kelas_filter] if kelas_filter else ['X', 'XI', 'XII']):
            rows = get_absensi_summary(kelas=kelas)
            if rows:
                df = pd.DataFrame([{'Nama': r['nama'], 'Hadir': r['hadir'], 'Sakit': r['sakit'],
                    'Izin': r['izin'], 'Alpha': r['alpha'], 'Total': r['total'],
                    '% Hadir': round(r['hadir']/r['total']*100, 1)} for r in rows])
                df.to_excel(writer, sheet_name=f'Rekap {kelas}', index=False)
                ws = writer.sheets[f'Rekap {kelas}']
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or '')) for c in col) + 4
            detail = get_absensi_rekap(kelas=kelas)
            if detail:
                df = pd.DataFrame([{'Tanggal': d['tanggal'], 'Nama': d['nama'],
                    'Status': d['status'], 'Keterangan': d['keterangan'] or ''} for d in detail])
                df.to_excel(writer, sheet_name=f'Detail {kelas}', index=False)
                ws = writer.sheets[f'Detail {kelas}']
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or '')) for c in col) + 4
    buf.seek(0)
    fname = f'Demo_Absensi_{kelas_filter or "Semua"}_{date.today()}.xlsx'
    return send_file(buf, as_attachment=True, download_name=fname,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ── Changelog ────────────────────────────────────────────────────────────────

VERSIONS = [
    {
        'versi': 'v3.0.0', 'tanggal': '2025-07-14', 'label': 'Terbaru',
        'label_color': 'success', 'judul': 'Kelola Nilai Dinamis', 'icon': 'journal-plus',
        'sections': [
            ('Tab Kelola Nilai (Guru)', [
                'Input nilai baru: PTS, Latihan Harian, UTS, UAS, Tugas, Praktik',
                'Tambah jenis nilai custom dengan "+ Jenis Baru..."',
                'Form: pilih kelas → tanggal → jenis → muat siswa → isi nilai → simpan',
                'Filter real-time tabel nilai (kelas, jenis, nama)',
                'Hapus per baris untuk koreksi data',
                'Export semua nilai ke satu file Excel',
            ]),
            ('Halaman Siswa', [
                'Tab PTS — nilai dari data tersimpan',
                'Tab Nilai Lainnya — latihan, tugas, dll dari guru',
            ]),
        ]
    },
    {
        'versi': 'v2.0.0', 'tanggal': '2025-07-10', 'label': None, 'label_color': None,
        'judul': 'Login, Role & Admin Panel', 'icon': 'shield-lock-fill',
        'sections': [
            ('Autentikasi', ['Login username & password', 'Role: Guru dan Siswa', 'Akun default guru: guru / guru123']),
            ('Tab Admin', ['Manajemen akun: tambah, hapus, reset password', 'SQL editor untuk query database']),
            ('Export Data', ['Export nilai ke Excel', 'Export absensi rekap + detail']),
        ]
    },
    {
        'versi': 'v1.0.0', 'tanggal': '2025-07-05', 'label': None, 'label_color': None,
        'judul': 'Rilis Pertama', 'icon': 'mortarboard-fill',
        'sections': [
            ('Dashboard Nilai PTS', ['Statistik per kelas', 'Chart distribusi grade', 'Tabel ranking siswa']),
            ('Absensi Siswa', ['Input absensi Hadir/Sakit/Izin/Alpha', 'Rekap kumulatif per siswa']),
        ]
    },
]

ROADMAP = [
    'Import nilai dari Excel (bulk upload)',
    'Grafik perkembangan nilai per siswa (line chart)',
    'Cetak rapor per siswa (PDF)',
    'Notifikasi untuk siswa dengan kehadiran rendah',
    'Backup & restore database',
    'Multi-semester support',
]

@app.route('/changelog')
@login_required
def changelog():
    return render_template('changelog.html', versions=VERSIONS, roadmap=ROADMAP,
                           latest=VERSIONS[0]['versi'])

if __name__ == '__main__':
    init_db()
    seed_demo()
    port = int(os.environ.get('PORT', 5000))
    print('\n' + '='*55)
    print('  Dashboard Nilai & Absensi - MODE DEMO')
    print('='*55)
    print(f'  URL   : http://localhost:{port}')
    print('  Guru  : guru / guru123')
    print('  Siswa : ahmad / siswa123  (contoh Kelas X)')
    print('          putri / siswa123  (contoh Kelas XI)')
    print('          edi   / siswa123  (contoh Kelas XII)')
    print('='*55 + '\n')
    app.run(debug=False, host='0.0.0.0', port=port)
