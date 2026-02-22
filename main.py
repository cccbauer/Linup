import flet as ft
from collections import deque
import sqlite3
import os
from datetime import datetime
import asyncio

# --- CONFIGURACIÓN DE GRUPOS ---
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
GRUPOS_MAESTROS = {
    '34': {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34},
    '35': {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35},
    '36': {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36},
    '1a': set(range(1, 13)), '2a': set(range(13, 25)), '3a': set(range(25, 37)),
    'Z0': {0, 3, 12, 15, 26, 32, 35},
    'ZG': {0, 2, 3, 4, 7, 12, 15, 18, 21, 19, 22, 25, 26, 28, 29, 31, 32, 35},
    'ZP': {5, 8, 10, 11, 13, 16, 23, 24, 27, 30, 33, 36},
    'H':  {1, 6, 9, 14, 17, 20, 31, 34},
    'T1': {0, 2, 4, 6, 13, 15, 17, 19, 21, 25, 27, 32, 34},
    'T2': {1, 5, 8, 10, 11, 16, 20, 23, 24, 30, 33, 36},
    'T3': {0, 3, 7, 9, 12, 14, 18, 22, 26, 28, 29, 31, 35},
}
PROG_FIBO = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
C_COL, C_DOC, C_SEC, C_SET = '#00d2ff', '#2ecc71', '#e67e22', '#9b59b6'
NUM_COLS = 20


class LinupApp:
    def __init__(self, page: ft.Page):
        self.page = page

        self.mixer_btns: dict = {}
        self.lbl_bank = None
        self.lbl_inv  = None
        self.lbl_pl   = None
        self.sug_row  = None
        self.btn_inv  = None
        self.reg_rows_box   = None
        self.reg_header_row = None
        self._on_game_screen = False

        self.page.title      = "Linup v11.2"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor    = '#1a1a1a'
        self.page.padding    = 0
        self.page.scroll     = None
        self.page.on_resized = self._on_resize

        self.root = ft.Container(expand=True, bgcolor='#1a1a1a')
        self.page.add(self.root)
        self.page.update()

        self.init_db()
        self.reset_variables()
        self.show_main_menu()

    # ──────────────────────────────────────────────────────────────────
    # FUENTE — tamaño fijo 15 para todos los botones
    # ──────────────────────────────────────────────────────────────────
    def _txt(self, label, size=15, bold=True):
        """ft.Text para content= de ElevatedButton. Default size=15."""
        return ft.Text(
            label,
            size=size,
            weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
            text_align=ft.TextAlign.CENTER,
        )

    # ──────────────────────────────────────────────────────────────────
    # ANCHO DE COLUMNA ADAPTABLE
    # ──────────────────────────────────────────────────────────────────
    def _col_width(self):
        w = self.page.width or 360
        return max(13, int((w - 4) / NUM_COLS))

    def _on_resize(self, e):
        if self._on_game_screen and self.reg_rows_box is not None:
            self.update_registration_table()

    # ──────────────────────────────────────────────────────────────────
    # BASE DE DATOS
    # ──────────────────────────────────────────────────────────────────
    def init_db(self):
        self.db_error = None
        # Candidate paths in priority order — Android needs app_support_path
        candidates = []
        asp = getattr(self.page, 'app_support_path', None)
        if asp:
            candidates.append(os.path.join(str(asp), "linup_data"))
        candidates += [
            os.path.join(os.path.expanduser("~"), "linup_data"),
            os.path.join(os.getcwd(), "linup_data"),
            os.path.join("/tmp", "linup_data"),
        ]
        self.db_path = None
        for data_dir in candidates:
            try:
                os.makedirs(data_dir, exist_ok=True)
                db_path = os.path.join(data_dir, "linup_data.db")
                conn = sqlite3.connect(db_path)
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS sesiones "
                    "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    " mesa TEXT, fecha TEXT, profit REAL, "
                    " banca_inicial REAL, banca_final REAL)"
                )
                conn.commit()
                try:
                    conn.execute("ALTER TABLE sesiones ADD COLUMN banca_inicial REAL")
                    conn.commit()
                except Exception:
                    pass  # columna ya existe
                conn.close()
                self.db_path = db_path  # éxito
                break
            except Exception as ex:
                self.db_error = str(ex)
                continue
        if not self.db_path:
            self.db_error = f"Todos los paths fallaron. Último: {self.db_error}"

    def _get_conn(self):
        if not self.db_path:
            return None
        try:
            return sqlite3.connect(self.db_path)
        except Exception:
            return None

    def _guardar_sesion(self):
        """Guarda sesion. Retorna (True, None) o (False, mensaje_error)."""
        try:
            if not self.db_path:
                init_err = getattr(self, "db_error", "desconocido")
                raise Exception(f"BD no disponible. init_db error: {init_err}")
            conn = sqlite3.connect(self.db_path)
            try:
                profit = round(float(self.banca_actual - self.banca_inicial), 2)
                fecha  = datetime.now().strftime("%d/%m %H:%M")
                conn.execute(
                    "INSERT INTO sesiones "
                    "(mesa, fecha, profit, banca_inicial, banca_final) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (str(self.nombre_mesa), fecha, profit,
                     round(float(self.banca_inicial), 2),
                     round(float(self.banca_actual),  2))
                )
                conn.commit()
                return True, None
            finally:
                conn.close()
        except Exception as ex:
            return False, str(ex)

    # ──────────────────────────────────────────────────────────────────
    # ESTADO
    # ──────────────────────────────────────────────────────────────────
    def reset_variables(self):
        self.banca_inicial    = 100.0
        self.banca_actual     = 100.0
        self.idx_fibo         = 0
        self.nivel_martingala = 0
        self.activa           = False
        self.grupos_activos   = []
        self.history_nums     = []
        self.sliding_window   = deque(maxlen=6)
        self.val_fin          = 0.10
        self.val_fout         = 0.30
        self.nombre_mesa      = "MESA 1"

    # ──────────────────────────────────────────────────────────────────
    # NAVEGACION
    # ──────────────────────────────────────────────────────────────────
    def _set_view(self, content: ft.Control):
        self.root.content = content
        self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # MENU PRINCIPAL
    # ──────────────────────────────────────────────────────────────────
    def show_main_menu(self, e=None):
        self._on_game_screen = False
        self._set_view(
            ft.Container(
                bgcolor='#1a1a1a', expand=True, padding=20,
                content=ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Linup", color='#3498db', size=32,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "NUEVA SESION", on_click=self.handle_new_session,
                            width=280, height=60,
                            style=ft.ButtonStyle(bgcolor='#27ae60',
                                                 color=ft.Colors.WHITE),
                        ),
                        ft.ElevatedButton(
                            "HISTORIAL / CARGAR", on_click=self.handle_show_history,
                            width=280, height=60,
                            style=ft.ButtonStyle(bgcolor='#2980b9',
                                                 color=ft.Colors.WHITE),
                        ),
                    ],
                ),
            )
        )

    # ──────────────────────────────────────────────────────────────────
    # HISTORIAL
    # ──────────────────────────────────────────────────────────────────
    def handle_show_history(self, e=None):
        rows = []
        conn = self._get_conn()
        if conn:
            try:
                cursor = conn.cursor()
                try:
                    cursor.execute("ALTER TABLE sesiones ADD COLUMN banca_inicial REAL")
                    conn.commit()
                except Exception:
                    pass
                cursor.execute(
                    "SELECT mesa, profit, banca_inicial, banca_final "
                    "FROM sesiones ORDER BY id DESC LIMIT 20"
                )
                for mesa, profit, b_ini, b_final in cursor.fetchall():
                    b_final = b_final or 0.0
                    b_ini   = b_ini or b_final or 1.0
                    efec    = (profit / b_ini * 100) if b_ini != 0 else 0
                    color   = '#2ecc71' if profit >= 0 else '#e74c3c'
                    txt     = f"{mesa}  |  BANK: ${b_final:.2f}  |  EFEC: {efec:+.1f}%"

                    def make_loader(m, bi, bf):
                        def loader(ev):
                            self.nombre_mesa   = str(m)
                            self.banca_inicial = float(bi)
                            self.banca_actual  = float(bf)
                            self.render_setup_form(True)
                        return loader

                    rows.append(
                        ft.ElevatedButton(
                            txt, on_click=make_loader(mesa, b_ini, b_final),
                            width=340, height=60,
                            style=ft.ButtonStyle(bgcolor='#222222', color=color),
                        )
                    )
            except Exception as ex:
                rows.append(ft.Text(f"Error: {ex}", color='#e74c3c'))
            finally:
                conn.close()

        if not rows:
            rows.append(ft.Text("Sin sesiones guardadas.", color='#7f8c8d'))

        self._set_view(
            ft.Container(
                bgcolor='#1a1a1a', expand=True,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.Container(
                            bgcolor='#2c3e50', padding=8,
                            content=ft.ElevatedButton(
                                "VOLVER", on_click=self.show_main_menu,
                                style=ft.ButtonStyle(bgcolor='#34495e',
                                                     color=ft.Colors.WHITE),
                            ),
                        ),
                        ft.ListView(controls=rows, expand=True,
                                    spacing=4, padding=10),
                    ],
                ),
            )
        )

    # ──────────────────────────────────────────────────────────────────
    # FORMULARIO DE CONFIGURACION
    # ──────────────────────────────────────────────────────────────────
    def handle_new_session(self, e=None):
        self.reset_variables()
        self.render_setup_form(False)

    def render_setup_form(self, is_continue: bool):
        self.table_input = ft.TextField(
            value=str(self.nombre_mesa),
            bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, height=45,
        )
        self.banca_input = ft.TextField(
            value=str(self.banca_actual),
            bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, height=45,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.fin_input = ft.TextField(
            value=str(self.val_fin),
            bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, height=45,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.fout_input = ft.TextField(
            value=str(self.val_fout),
            bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, height=45,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        btn_txt = "REANUDAR MESA" if is_continue else "ABRIR MESA"
        self._set_view(
            ft.Container(
                bgcolor='#1a1a1a', expand=True, padding=20,
                content=ft.ListView(
                    expand=True,
                    controls=[
                        ft.ElevatedButton(
                            "CANCELAR", on_click=self.show_main_menu,
                            style=ft.ButtonStyle(bgcolor='#c0392b',
                                                 color=ft.Colors.WHITE),
                        ),
                        ft.Container(height=10),
                        ft.Text("NOMBRE MESA:", color=ft.Colors.WHITE),
                        self.table_input,
                        ft.Text("BANK:", color=ft.Colors.WHITE),
                        self.banca_input,
                        ft.Text("FICHA IN:", color=ft.Colors.WHITE),
                        self.fin_input,
                        ft.Text("FICHA OUT (BASE):", color=ft.Colors.WHITE),
                        self.fout_input,
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            btn_txt, on_click=self.iniciar_ciclo,
                            height=70, expand=True,
                            style=ft.ButtonStyle(bgcolor='#27ae60',
                                                 color=ft.Colors.WHITE),
                        ),
                    ],
                ),
            )
        )

    # ──────────────────────────────────────────────────────────────────
    # INICIAR CICLO
    # ──────────────────────────────────────────────────────────────────
    def iniciar_ciclo(self, e=None):
        try:
            self.nombre_mesa   = str(self.table_input.value).upper() or "MESA 1"
            self.banca_inicial = float(self.banca_input.value or 100)
            self.banca_actual  = self.banca_inicial
            self.val_fin       = float(self.fin_input.value  or 0.1)
            self.val_fout      = float(self.fout_input.value or 0.3)
        except Exception:
            pass
        self.show_game_screen()

    # ─────────────────────────────────────────────────────────────────
    # FINALIZAR — popup resumen → guarda → OK regresa al menú
    # ─────────────────────────────────────────────────────────────────
    def finalizar_sesion(self, e=None):
        profit   = round(self.banca_actual - self.banca_inicial, 2)
        pl_pct   = (profit / self.banca_inicial * 100) if self.banca_inicial != 0 else 0
        positivo = profit >= 0
        color    = '#2ecc71' if positivo else '#e74c3c'
        signo    = "+" if positivo else ""

        # Guardar en BD
        ok, err_msg    = self._guardar_sesion()
        guardado_txt   = "✅ Guardado en historial" if ok else f"❌ Error: {err_msg}"
        guardado_color = '#2ecc71' if ok else '#e74c3c'

        dlg = ft.AlertDialog(modal=True, bgcolor='#1e1e1e')

        def cerrar(ev):
            dlg.open = False
            self.page.update()
            self.show_main_menu()

        dlg.title = ft.Text(
            f"RESUMEN  {self.nombre_mesa}",
            color='#3498db', size=16, weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        dlg.content = ft.Column(
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Divider(color='#444444'),
                ft.Text(f"Bank inicial:  ${self.banca_inicial:.2f}",
                        color=ft.Colors.WHITE, size=14),
                ft.Text(f"Bank final:    ${self.banca_actual:.2f}",
                        color=ft.Colors.WHITE, size=14),
                ft.Container(height=8),
                ft.Text(
                    f"P/L:  {signo}${profit:.2f}   ({signo}{pl_pct:.1f}%)",
                    color=color, size=20, weight=ft.FontWeight.BOLD,
                ),
                ft.Container(height=10),
                ft.Text(guardado_txt, color=guardado_color, size=13),
            ],
        )
        dlg.actions = [
            ft.ElevatedButton(
                content=ft.Text("OK", size=15, weight=ft.FontWeight.BOLD),
                on_click=cerrar,
                expand=True,
                style=ft.ButtonStyle(bgcolor=color, color=ft.Colors.WHITE),
            )
        ]
        dlg.actions_alignment = ft.MainAxisAlignment.CENTER

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # PANTALLA DE JUEGO
    # ──────────────────────────────────────────────────────────────────
    def show_game_screen(self):
        self._on_game_screen = True

        # ── Barra de mesa ──────────────────────────────────────────
        mesa_bar = ft.Container(
            bgcolor='#000000',
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            content=ft.Text(f"  {self.nombre_mesa}", color='#3498db',
                            weight=ft.FontWeight.BOLD, size=11),
        )

        # ── Stats bar ──────────────────────────────────────────────
        self.lbl_bank = ft.Text(
            f"BANK: ${self.banca_actual:.2f}",
            color='#2ecc71', weight=ft.FontWeight.BOLD, size=10, expand=True,
        )
        self.lbl_inv = ft.Text(
            "INV: $0.00",
            color='#f1c40f', weight=ft.FontWeight.BOLD, size=10, expand=True,
            text_align=ft.TextAlign.CENTER,
        )
        self.lbl_pl = ft.Text(
            "P/L: 0.0%",
            color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=10, expand=True,
            text_align=ft.TextAlign.RIGHT,
        )
        stats_bar = ft.Container(
            bgcolor='#1e1e1e', padding=5,
            content=ft.Row(controls=[self.lbl_bank, self.lbl_inv, self.lbl_pl]),
        )

        # ── Sugerencias ────────────────────────────────────────────
        self.sug_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    content=self._txt("---", size=12),
                    expand=True, height=35,
                    style=ft.ButtonStyle(bgcolor='#34495e', color=ft.Colors.WHITE),
                )
                for _ in range(4)
            ],
            spacing=2,
        )
        sug_bar = ft.Container(
            bgcolor='#2c3e50', padding=4, height=44,
            content=self.sug_row,
        )

        # ── Mixer ──────────────────────────────────────────────────
        self.mixer_btns = {}
        cats = [
            (['34', '35', '36'], C_COL),
            (['1a', '2a', '3a'], C_DOC),
            (['Z0', 'ZG', 'ZP', 'H'], C_SEC),
            (['T1', 'T2', 'T3'], C_SET),
        ]
        mixer_rows = []
        for grps, col in cats:
            row_btns = []
            for g in grps:
                btn = ft.ElevatedButton(
                    content=self._txt(g),
                    data={'name': g, 'color': col},
                    on_click=self.seleccionar_mixer,
                    expand=True, height=40,
                    style=ft.ButtonStyle(
                        bgcolor=col, color=ft.Colors.WHITE,
                        animation_duration=400,
                        overlay_color={
                            ft.ControlState.PRESSED: ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                        },
                    ),
                )
                self.mixer_btns[g] = btn
                row_btns.append(btn)
            mixer_rows.append(ft.Row(controls=row_btns, spacing=2))

        mixer_box = ft.Container(
            padding=ft.padding.symmetric(horizontal=2),
            content=ft.Column(controls=mixer_rows, spacing=2),
        )

        # ── Controles ──────────────────────────────────────────────
        self.btn_inv = ft.ElevatedButton(
            content=self._txt("INVERTIR"),
            on_click=self.confirmar_manual,
            expand=2, height=45,
            style=ft.ButtonStyle(bgcolor='#2ecc71', color=ft.Colors.WHITE,
                                 animation_duration=400),
        )
        btn_corr = ft.ElevatedButton(
            content=self._txt("CORR"),
            on_click=self.corregir_ultimo,
            expand=1, height=45,
            style=ft.ButtonStyle(bgcolor='#f39c12', color=ft.Colors.WHITE,
                                 animation_duration=400),
        )
        btn_fin = ft.ElevatedButton(
            content=self._txt("FINALIZAR"),
            on_click=self.finalizar_sesion,
            expand=1, height=45,
            style=ft.ButtonStyle(bgcolor='#e74c3c', color=ft.Colors.WHITE,
                                 animation_duration=400),
        )
        ctrl_bar = ft.Container(
            padding=ft.padding.symmetric(horizontal=4, vertical=4),
            content=ft.Row(controls=[self.btn_inv, btn_corr, btn_fin], spacing=4),
        )

        # ── Teclado numérico ───────────────────────────────────────
        teclado_controls = [
            ft.Row(controls=[
                ft.ElevatedButton(
                    content=self._txt("0"),
                    data=0, on_click=self.process_number,
                    height=45, expand=True,
                    style=ft.ButtonStyle(
                        bgcolor='#27ae60', color=ft.Colors.WHITE,
                        animation_duration=400,
                        overlay_color={
                            ft.ControlState.PRESSED: ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                        },
                    ),
                )
            ])
        ]
        for i in range(12):
            row_btns = []
            for j in range(1, 4):
                n = (i * 3) + j
                row_btns.append(
                    ft.ElevatedButton(
                        content=self._txt(str(n)),
                        data=n, on_click=self.process_number,
                        expand=True, height=40,
                        style=ft.ButtonStyle(
                            bgcolor='#cc0000' if n in ROJOS else '#222222',
                            color=ft.Colors.WHITE,
                            animation_duration=400,
                            overlay_color={
                                ft.ControlState.PRESSED: ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                            },
                        ),
                    )
                )
            teclado_controls.append(ft.Row(controls=row_btns, spacing=2))

        teclado = ft.Container(
            bgcolor='#0e3d24', padding=5, height=620,
            content=ft.Column(controls=teclado_controls, spacing=2),
        )

        # ── Bitacora ───────────────────────────────────────────────
        self.reg_header_row = ft.Row(controls=[], spacing=0)
        self.reg_rows_box   = ft.Column(controls=[], spacing=0)
        self._rebuild_table_header()

        bitacora = ft.Container(
            height=170, bgcolor='#0d0d0d',
            content=ft.Row(
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Column(
                        controls=[self.reg_header_row, self.reg_rows_box],
                        spacing=0, tight=True,
                    )
                ],
            ),
        )

        # ── Layout final ───────────────────────────────────────────
        self._set_view(
            ft.Container(
                bgcolor='#121212', expand=True,
                content=ft.Column(
                    expand=True, spacing=0,
                    controls=[
                        mesa_bar, stats_bar, sug_bar,
                        mixer_box, ctrl_bar,
                        ft.Container(
                            expand=True,
                            content=ft.ListView(expand=True, controls=[teclado]),
                        ),
                        bitacora,
                    ],
                ),
            )
        )

        self.actualizar_sugerencias()

    # ──────────────────────────────────────────────────────────────────
    # BITACORA
    # ──────────────────────────────────────────────────────────────────
    def _rebuild_table_header(self):
        cw = self._col_width()
        h_list = ["N","R","N","P","I","B","A",
                  "34","35","36","1a","2a","3a",
                  "Z0","ZG","ZP","H","T1","T2","T3"]
        self.reg_header_row.controls = [
            ft.Text(h, width=cw, color='#7f8c8d',
                    text_align=ft.TextAlign.CENTER,
                    size=7, weight=ft.FontWeight.BOLD)
            for h in h_list
        ]

    def update_registration_table(self):
        if self.reg_rows_box is None:
            return
        cw = self._col_width()
        self._rebuild_table_header()
        self.reg_rows_box.controls.clear()
        s = "■"
        for n in self.history_nums[-8:]:
            cells = [
                (str(n),                                      '#f1c40f'),
                (s if n in ROJOS else "",                     '#ff4d4d'),
                (s if (n!=0 and n not in ROJOS) else "",      ft.Colors.WHITE),
                (s if (n!=0 and n%2==0) else "",              '#3498db'),
                (s if (n%2!=0) else "",                       '#f39c12'),
                (s if (1<=n<=18) else "",                     ft.Colors.WHITE),
                (s if (19<=n<=36) else "",                    ft.Colors.WHITE),
                (s if n in GRUPOS_MAESTROS['34'] else "",     C_COL),
                (s if n in GRUPOS_MAESTROS['35'] else "",     C_COL),
                (s if n in GRUPOS_MAESTROS['36'] else "",     C_COL),
                (s if n in GRUPOS_MAESTROS['1a'] else "",     C_DOC),
                (s if n in GRUPOS_MAESTROS['2a'] else "",     C_DOC),
                (s if n in GRUPOS_MAESTROS['3a'] else "",     C_DOC),
                (s if n in GRUPOS_MAESTROS['Z0'] else "",     C_SEC),
                (s if n in GRUPOS_MAESTROS['ZG'] else "",     C_SEC),
                (s if n in GRUPOS_MAESTROS['ZP'] else "",     C_SEC),
                (s if n in GRUPOS_MAESTROS['H']  else "",     C_SEC),
                (s if n in GRUPOS_MAESTROS['T1'] else "",     C_SET),
                (s if n in GRUPOS_MAESTROS['T2'] else "",     C_SET),
                (s if n in GRUPOS_MAESTROS['T3'] else "",     C_SET),
            ]
            self.reg_rows_box.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(txt, width=cw, color=col,
                                text_align=ft.TextAlign.CENTER,
                                size=8, weight=ft.FontWeight.BOLD)
                        for txt, col in cells
                    ],
                    spacing=0,
                )
            )
        self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # FEEDBACK VISUAL
    # ──────────────────────────────────────────────────────────────────
    def _darken_color(self, hex_color, factor=0.7):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f'#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}'
        return hex_color

    def _flash_button(self, btn, original_color, duration_ms=300):
        flash_color = self._darken_color(original_color, 0.6)
        async def _animate():
            btn.style.bgcolor = flash_color
            self.page.update()
            await asyncio.sleep(duration_ms / 1000)
            btn.style.bgcolor = original_color
            self.page.update()
        asyncio.create_task(_animate())

    # ──────────────────────────────────────────────────────────────────
    # LÓGICA DE JUEGO
    # ──────────────────────────────────────────────────────────────────

    # Grupos que se apuestan número a número con val_fin
    GRUPOS_STRAIGHT = {'Z0', 'ZG', 'ZP', 'H', 'T1', 'T2', 'T3'}

    # Progresión para 2 grupos outside (columnas/docenas)
    # Total bet × val_fout: 0.6, 1.8, 2.7, 5.4, 8.1, 16.2 ...
    PROG_2_OUT = [2, 6, 9, 18, 27, 54, 81]

    def _is_outside(self):
        """True si todos los grupos activos son columnas o docenas."""
        return all(g not in self.GRUPOS_STRAIGHT for g in self.grupos_activos)

    def _group_cost(self, g):
        """
        Costo base de UN grupo sin multiplicador de progresión.
        - Columnas/docenas: val_fout
        - Zonas/sectores:   val_fin × cantidad de números del grupo
        """
        if g in self.GRUPOS_STRAIGHT:
            return self.val_fin * len(GRUPOS_MAESTROS[g])
        return self.val_fout

    def _compute_bet(self):
        """
        Devuelve (total_cost, per_group_win_payout) según tipo y progresión.
        """
        n = len(self.grupos_activos)
        if n == 0:
            return 0.0, 0.0

        if self._is_outside():
            if n == 1:
                multi      = PROG_FIBO[self.idx_fibo]
                total      = self.val_fout * multi
                win_payout = total * 3          # 3× la ficha apostada
            else:
                idx        = min(self.nivel_martingala, len(self.PROG_2_OUT) - 1)
                total      = self.val_fout * self.PROG_2_OUT[idx]
                win_payout = (total / n) * 3    # 3× la ficha por grupo ganador
        else:
            # Zonas / sectores: val_fin × len(grupo) por grupo
            multi      = PROG_FIBO[self.idx_fibo] if n == 1 else (2 ** self.nivel_martingala)
            total      = sum(self._group_cost(g) * multi for g in self.grupos_activos)
            win_payout = (total / n) * 3

        return total, win_payout

    def process_number(self, e):
        try:
            btn = e.control
            self._flash_button(btn, btn.style.bgcolor, 300)

            num = int(e.control.data)
            if self.activa:
                n                  = len(self.grupos_activos)
                total_cost, win_py = self._compute_bet()
                self.banca_actual -= total_cost

                if any(num in GRUPOS_MAESTROS[g] for g in self.grupos_activos):
                    self.banca_actual += win_py
                    self.idx_fibo         = 0
                    self.nivel_martingala = 0
                else:
                    if n == 1:
                        if self.idx_fibo < len(PROG_FIBO) - 1:
                            self.idx_fibo += 1
                    else:
                        self.nivel_martingala += 1
                self.activa         = False
                self.grupos_activos = []
                self.limpiar_seleccion_visual()
            else:
                self.banca_actual -= self.val_fin
                if num in ROJOS:
                    self.banca_actual += (self.val_fin * 2)

            self.history_nums.append(num)
            self.sliding_window.append(num)
            self.update_ui()
            self.update_registration_table()
            self.actualizar_sugerencias()
        except Exception:
            pass

    def seleccionar_mixer(self, e):
        g          = e.control.data['name']
        base_color = e.control.data['color']

        if g in self.grupos_activos:
            self.grupos_activos.remove(g)
            e.control.style = ft.ButtonStyle(
                bgcolor=base_color, color=ft.Colors.WHITE,
                animation_duration=400,
                overlay_color={ft.ControlState.PRESSED: ft.Colors.with_opacity(0.4, ft.Colors.WHITE)},
            )
        elif len(self.grupos_activos) < 2:
            self.grupos_activos.append(g)
            e.control.style = ft.ButtonStyle(
                bgcolor=base_color, color='#f1c40f',
                animation_duration=400,
                overlay_color={ft.ControlState.PRESSED: ft.Colors.with_opacity(0.4, ft.Colors.WHITE)},
            )
        e.control.update()
        self.update_inv_label()
        self.lbl_inv.update()

    def confirmar_manual(self, e=None):
        if self.grupos_activos:
            self.activa = True
            self.btn_inv.style = ft.ButtonStyle(bgcolor='#3498db', color=ft.Colors.WHITE,
                                                animation_duration=400)
            self.btn_inv.update()
            self.update_inv_label()
            self.lbl_inv.update()

    def auto_invertir_sug(self, grupos):
        self.limpiar_seleccion_visual()
        self.grupos_activos = list(grupos)
        self.activa         = True
        self.btn_inv.style = ft.ButtonStyle(bgcolor='#3498db', color=ft.Colors.WHITE,
                                            animation_duration=400)
        self.btn_inv.update()
        self.update_inv_label()
        self.lbl_inv.update()

    # ──────────────────────────────────────────────────────────────────
    # SUGERENCIAS
    # Condición para mostrar: el 2.º grupo supera en frecuencia al 3.º
    # → cubre "dos iguales arriba" y "uno mayor+uno menor que el 3.º"
    # Si los tres/cuatro están empatados → "---" (sin sugerencia)
    # ──────────────────────────────────────────────────────────────────
    def _make_sug_handler(self, g_par):
        def handler(ev):
            self.auto_invertir_sug(g_par)
        return handler

    def actualizar_sugerencias(self):
        cats = [
            (['34', '35', '36'], C_COL),
            (['1a', '2a', '3a'], C_DOC),
            (['Z0', 'ZG', 'ZP', 'H'], C_SEC),
            (['T1', 'T2', 'T3'], C_SET),
        ]

        if len(self.sliding_window) < 6:
            faltan = 6 - len(self.sliding_window)
            self.sug_row.controls = [
                ft.ElevatedButton(
                    content=self._txt(f"({faltan} más)", size=12),
                    expand=True, height=35,
                    style=ft.ButtonStyle(bgcolor='#34495e', color=ft.Colors.WHITE),
                )
                for _ in range(4)
            ]
            self.sug_row.update()
            return

        new_btns = []
        for grupos, color in cats:
            stats = sorted(
                [{'g': g,
                  'p': sum(1 for n in self.sliding_window
                           if n in GRUPOS_MAESTROS[g]) / 6}
                 for g in grupos],
                key=lambda x: x['p'], reverse=True,
            )
            # Sugerencia válida solo si el #2 supera al #3
            # Y nunca sugerir ZG+ZP (demasiadas fichas)
            PAIR_BLOQUEADO = {'ZG', 'ZP'}
            g_par_candidato = {stats[0]['g'], stats[1]['g']}
            es_par_bloqueado = g_par_candidato == PAIR_BLOQUEADO

            if stats[1]['p'] > stats[2]['p'] and not es_par_bloqueado:
                g_par = [stats[0]['g'], stats[1]['g']]
                label = f"{g_par[0]}+{g_par[1]}"
                bg    = color
                click = self._make_sug_handler(g_par)
            else:
                label = "---"
                bg    = '#34495e'
                click = None

            new_btns.append(
                ft.ElevatedButton(
                    content=self._txt(label, size=12),
                    expand=True, height=35,
                    on_click=click,
                    style=ft.ButtonStyle(bgcolor=bg, color=ft.Colors.WHITE),
                )
            )

        self.sug_row.controls = new_btns
        self.sug_row.update()

    # ──────────────────────────────────────────────────────────────────

    def limpiar_seleccion_visual(self):
        if self.btn_inv:
            self.btn_inv.style = ft.ButtonStyle(bgcolor='#2ecc71', color=ft.Colors.WHITE,
                                                animation_duration=400)
            self.btn_inv.update()
        for b in self.mixer_btns.values():
            base_color = b.data['color']
            b.style = ft.ButtonStyle(
                bgcolor=base_color, color=ft.Colors.WHITE,
                animation_duration=400,
                overlay_color={ft.ControlState.PRESSED: ft.Colors.with_opacity(0.4, ft.Colors.WHITE)},
            )
            b.update()
        self.grupos_activos = []
        self.update_inv_label()
        if self.lbl_inv:
            self.lbl_inv.update()

    def update_inv_label(self):
        if not self.lbl_inv:
            return
        if self.activa or self.grupos_activos:
            total, _ = self._compute_bet()
            self.lbl_inv.value = f"INV: ${total:.2f}"
        else:
            self.lbl_inv.value = "INV: $0.00"

    def update_ui(self):
        if not self.lbl_bank:
            return
        pl     = self.banca_actual - self.banca_inicial
        pl_pct = (pl / self.banca_inicial * 100) if self.banca_inicial != 0 else 0
        self.lbl_bank.value = f"BANK: ${self.banca_actual:.2f}"
        self.lbl_pl.value   = f"P/L: {pl_pct:+.1f}%"
        self.lbl_pl.color   = '#2ecc71' if pl >= 0 else '#e74c3c'
        self.update_inv_label()
        self.page.update()

    def corregir_ultimo(self, e=None):
        if self.history_nums:
            self.history_nums.pop()
            if self.idx_fibo > 0:
                self.idx_fibo -= 1
            if self.nivel_martingala > 0:
                self.nivel_martingala -= 1
            self.update_ui()
            self.update_registration_table()


# ──────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────────────────────────────
def main(page: ft.Page):
    LinupApp(page)


ft.app(main)