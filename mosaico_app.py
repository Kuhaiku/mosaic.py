import sys
import os
import math
import ctypes
import subprocess
import json
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QRadioButton, QComboBox, 
                             QSpinBox, QDoubleSpinBox, QGraphicsView, QGraphicsScene, 
                             QMessageBox, QGroupBox, QFormLayout, QSplashScreen, QDialog, QLineEdit)
from PyQt6.QtGui import QPixmap, QPen, QColor, QPainter, QFont, QIcon
from PyQt6.QtCore import Qt, QRectF, QTimer
from PIL import Image

# Permite que o Pillow processe imagens gigantes sem erro de segurança
Image.MAX_IMAGE_PIXELS = None

# =====================================================================
# 1. TELA DE ATIVAÇÃO E VALIDAÇÃO DE LICENÇA VIA API (NODE.JS)
# =====================================================================
class TelaAtivacao(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ativação do Produto - Raposo.tech")
        self.setFixedSize(500, 250)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        
        self.hwid = self.obter_hwid()
        self.licenca_arquivo = "licenca_local.json"
        
        # --- CONFIGURAÇÃO DA API ---
        # Troque 'localhost' pelo IP ou Domínio do seu servidor quando colocar no ar
    # No Python (mosaico_app.py):
        self.api_url = "https://w-raposotechlicencas.velmc0.easypanel.host/api/validar-licenca"
        self.produto_id = 1 # ID do Gerador de Mosaicos no seu banco de dados
        
        self.initUI()

    def obter_hwid(self):
        try:
            # creationflags=subprocess.CREATE_NO_WINDOW impede que a tela preta do CMD pisque
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW
            return subprocess.check_output('wmic csproduct get uuid', creationflags=flags).decode().split('\n')[1].strip()
        except:
            return "HWID-NAO-DETECTADO"

    def initUI(self):
        layout = QVBoxLayout()
        
        lbl_info = QLabel("<b>Software não ativado ou licença expirada.</b><br>Insira sua chave de ativação para liberar o uso.")
        lbl_info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        form_layout = QFormLayout()
        
        self.input_hwid = QLineEdit()
        self.input_hwid.setText(self.hwid)
        self.input_hwid.setReadOnly(True)
        self.input_hwid.setStyleSheet("background-color: #eee; color: #333; font-weight: bold;")
        form_layout.addRow("Seu Dispositivo (HWID):", self.input_hwid)
        
        self.input_chave = QLineEdit()
        self.input_chave.setPlaceholderText("Ex: RAPOSO-MOSAICO-2026")
        form_layout.addRow("Chave de Ativação:", self.input_chave)
        
        layout.addLayout(form_layout)
        
        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.lbl_erro)
        
        btn_ativar = QPushButton("Verificar e Ativar")
        btn_ativar.setMinimumHeight(40)
        btn_ativar.setStyleSheet("background-color: #2E8B57; color: white; font-weight: bold;")
        btn_ativar.clicked.connect(self.tentar_ativar)
        layout.addWidget(btn_ativar)
        
        self.setLayout(layout)

    def tentar_ativar(self):
        chave_digitada = self.input_chave.text().strip()
        if not chave_digitada:
            self.lbl_erro.setText("Digite uma chave.")
            return

        self.lbl_erro.setText("Conectando ao servidor...")
        QApplication.processEvents()

        valido, msg = self.validar_online(chave_digitada)
        
        if valido:
            with open(self.licenca_arquivo, 'w') as f:
                json.dump({"chave": chave_digitada}, f)
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            self.lbl_erro.setText(f"Erro: {msg}")

    def validar_online(self, chave_digitada):
        payload = {
            "chave": chave_digitada,
            "hwid": self.hwid,
            "produto_id": self.produto_id
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=5)
            dados = response.json()
            
            if response.status_code == 200:
                return True, dados.get("message", "Sucesso")
            else:
                return False, dados.get("error", "Erro desconhecido retornado pelo servidor.")
                
        except requests.exceptions.RequestException:
            return False, "Sem conexão com o servidor de licenças. Verifique sua internet."

    def verificar_licenca_existente(self):
        if not os.path.exists(self.licenca_arquivo):
            return False
            
        try:
            with open(self.licenca_arquivo, 'r') as f:
                dados = json.load(f)
            chave = dados.get("chave", "")
            
            valido, _ = self.validar_online(chave)
            return valido
        except:
            return False


# =====================================================================
# 2. TELA DE CARREGAMENTO (SPLASH SCREEN)
# =====================================================================
class SplashScreen(QSplashScreen):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
        self.pixmap1 = self.gerar_imagem("icone.png", 1)
        self.pixmap2 = self.gerar_imagem("foto2.png", 2)
        
        self.setPixmap(self.pixmap1)
        
        QTimer.singleShot(3000, self.trocar_imagem)
        QTimer.singleShot(6000, self.iniciar_programa)

    def trocar_imagem(self):
        self.setPixmap(self.pixmap2)

    def iniciar_programa(self):
        self.main_window.show()
        self.close()

    def gerar_imagem(self, path, num):
        largura_max = 800
        altura_max = 600

        if os.path.exists(path):
            pixmap = QPixmap(path)
            return pixmap.scaled(largura_max, altura_max, 
                                 Qt.AspectRatioMode.KeepAspectRatio, 
                                 Qt.TransformationMode.SmoothTransformation)
        
        pixmap = QPixmap(largura_max, altura_max)
        cor = QColor("#2a2a2a") if num == 1 else QColor("#1e1e1e")
        pixmap.fill(cor)
        
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        texto = f"Carregando Raposo.tech...\nTela {num}/2 (Adicione {path} na pasta)"
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, texto)
        painter.end()
        return pixmap


# =====================================================================
# 3. APLICAÇÃO PRINCIPAL (GERADOR DE MOSAICOS)
# =====================================================================
class MosaicoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Mosaicos - Raposo.tech")
        self.setGeometry(100, 100, 1200, 800)
        
        # Define o ícone da janela
        self.setWindowIcon(QIcon("icone.png"))
        
        self.image_path = None
        self.original_pixmap = None
        
        self.paper_sizes = {
            "A4": (21.0, 29.7),
            "A3": (29.7, 42.0)
        }
        self.dpi = 300 
        
        self.initUI()
        self.mostrar_placeholder_vazio()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- PAINEL ESQUERDO (Controles) ---
        control_panel = QWidget()
        control_panel.setFixedWidth(360)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_load = QPushButton("Carregar Imagem")
        self.btn_load.setMinimumHeight(45)
        self.btn_load.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_load.clicked.connect(self.load_image)
        control_layout.addWidget(self.btn_load)

        paper_group = QGroupBox("Configurações do Papel")
        paper_layout = QFormLayout()
        
        self.cb_paper = QComboBox()
        self.cb_paper.addItems(["A4", "A3"])
        self.cb_paper.currentIndexChanged.connect(self.update_preview)
        
        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["Retrato", "Paisagem"])
        self.cb_orientation.currentIndexChanged.connect(self.update_preview)
        
        paper_layout.addRow("Tamanho:", self.cb_paper)
        paper_layout.addRow("Orientação:", self.cb_orientation)
        paper_group.setLayout(paper_layout)
        control_layout.addWidget(paper_group)

        method_group = QGroupBox("Método de Corte")
        method_layout = QVBoxLayout()
        
        self.radio_medida = QRadioButton("Medida Final Total (cm)")
        self.radio_medida.setChecked(True)
        self.radio_medida.toggled.connect(self.toggle_methods)
        
        self.radio_grade = QRadioButton("Grade (Linhas x Colunas de folhas)")
        self.radio_grade.toggled.connect(self.toggle_methods)
        
        method_layout.addWidget(self.radio_medida)
        
        self.medida_widget = QWidget()
        medida_form = QFormLayout(self.medida_widget)
        medida_form.setContentsMargins(0, 0, 0, 0)
        
        self.spin_width_cm = QDoubleSpinBox()
        self.spin_width_cm.setRange(1.0, 1000.0)
        self.spin_width_cm.setValue(100.0)
        self.spin_width_cm.setSuffix(" cm")
        self.spin_width_cm.valueChanged.connect(self.update_preview)
        
        self.spin_height_cm = QDoubleSpinBox()
        self.spin_height_cm.setRange(1.0, 1000.0)
        self.spin_height_cm.setValue(100.0)
        self.spin_height_cm.setSuffix(" cm")
        self.spin_height_cm.valueChanged.connect(self.update_preview)
        
        medida_form.addRow("Largura Total:", self.spin_width_cm)
        medida_form.addRow("Altura Total:", self.spin_height_cm)
        method_layout.addWidget(self.medida_widget)

        method_layout.addWidget(self.radio_grade)

        self.grade_widget = QWidget()
        grade_form = QFormLayout(self.grade_widget)
        grade_form.setContentsMargins(0, 0, 0, 0)
        
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 100)
        self.spin_cols.setValue(3)
        self.spin_cols.valueChanged.connect(self.update_preview)
        
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 100)
        self.spin_rows.setValue(3)
        self.spin_rows.valueChanged.connect(self.update_preview)
        
        grade_form.addRow("Colunas (Largura):", self.spin_cols)
        grade_form.addRow("Linhas (Altura):", self.spin_rows)
        method_layout.addWidget(self.grade_widget)
        self.grade_widget.setVisible(False)

        method_group.setLayout(method_layout)
        control_layout.addWidget(method_group)

        feedback_group = QGroupBox("Feedback de Proporção")
        feedback_layout = QVBoxLayout()
        self.lbl_prop_orig = QLabel("Proporção Original: -")
        self.lbl_prop_final = QLabel("Proporção Final: -")
        self.lbl_status_distorcao = QLabel("Aguardando imagem...")
        self.lbl_status_distorcao.setStyleSheet("color: gray;")
        
        feedback_layout.addWidget(self.lbl_prop_orig)
        feedback_layout.addWidget(self.lbl_prop_final)
        feedback_layout.addWidget(self.lbl_status_distorcao)
        feedback_group.setLayout(feedback_layout)
        control_layout.addWidget(feedback_group)

        self.lbl_info = QLabel("Páginas necessárias: 0\nTamanho final impresso: 0 x 0 cm")
        self.lbl_info.setStyleSheet("color: #333; font-size: 13px; margin-top: 5px;")
        control_layout.addWidget(self.lbl_info)

        self.btn_process = QPushButton("Processar e Salvar Recortes")
        self.btn_process.setMinimumHeight(50)
        self.btn_process.setStyleSheet("background-color: #2E8B57; color: white; font-weight: bold; font-size: 14px; border-radius: 4px;")
        self.btn_process.clicked.connect(self.process_image)
        self.btn_process.setEnabled(False)
        control_layout.addWidget(self.btn_process)

        main_layout.addWidget(control_panel)

        # --- PAINEL DIREITO (Preview Visual) ---
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background-color: #1e1e1e; border: 1px solid #444;")
        main_layout.addWidget(self.view)

    def mostrar_placeholder_vazio(self):
        self.scene.clear()
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor("#222222"))
        painter = QPainter(pixmap)
        painter.setPen(QColor("#777777"))
        painter.setFont(QFont("Arial", 16))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Nenhuma imagem carregada.\nClique no botão à esquerda para começar.")
        painter.end()
        self.scene.addPixmap(pixmap)
        self.view.fitInView(QRectF(0, 0, pixmap.width(), pixmap.height()), Qt.AspectRatioMode.KeepAspectRatio)

    def toggle_methods(self):
        is_medida = self.radio_medida.isChecked()
        self.medida_widget.setVisible(is_medida)
        self.grade_widget.setVisible(not is_medida)
        self.update_preview()

    def get_paper_size_cm(self):
        w, h = self.paper_sizes[self.cb_paper.currentText()]
        if self.cb_orientation.currentText() == "Paisagem":
            return h, w
        return w, h

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir Imagem", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.image_path = file_name
            self.original_pixmap = QPixmap(file_name)
            self.btn_process.setEnabled(True)
            self.update_preview()

    def calculate_grid(self):
        if not self.image_path:
            return 0, 0, 0, 0, 0, 0
            
        paper_w_cm, paper_h_cm = self.get_paper_size_cm()

        if self.radio_medida.isChecked():
            target_w_cm = self.spin_width_cm.value()
            target_h_cm = self.spin_height_cm.value()
            
            cols = math.ceil(target_w_cm / paper_w_cm)
            rows = math.ceil(target_h_cm / paper_h_cm)
            
            grid_w_cm = cols * paper_w_cm
            grid_h_cm = rows * paper_h_cm
            
            return cols, rows, grid_w_cm, grid_h_cm, target_w_cm, target_h_cm

        else:
            cols = self.spin_cols.value()
            rows = self.spin_rows.value()
            
            grid_w_cm = cols * paper_w_cm
            grid_h_cm = rows * paper_h_cm
            
            return cols, rows, grid_w_cm, grid_h_cm, grid_w_cm, grid_h_cm

    def update_preview(self):
        if not self.original_pixmap:
            return

        self.scene.clear()
        
        cols, rows, grid_w_cm, grid_h_cm, target_w_cm, target_h_cm = self.calculate_grid()
        
        pixmap_w = self.original_pixmap.width()
        pixmap_h = self.original_pixmap.height()
        
        self.scene.addPixmap(self.original_pixmap)
        
        prop_orig = pixmap_w / pixmap_h
        prop_final = target_w_cm / target_h_cm if target_h_cm > 0 else prop_orig
        
        desvio_percentual = ((prop_final / prop_orig) - 1) * 100

        self.lbl_prop_orig.setText(f"Proporção Original: 1 : {prop_orig:.2f}")
        self.lbl_prop_final.setText(f"Proporção Final: 1 : {prop_final:.2f}")

        if abs(desvio_percentual) <= 2.0:
            self.lbl_status_distorcao.setText("Tudo OK: Proporção Mantida")
            self.lbl_status_distorcao.setStyleSheet("color: #2E8B57; font-weight: bold;")
        else:
            tipo = "Achatada" if desvio_percentual < 0 else "Esticada"
            eixo = "Verticalmente" if desvio_percentual < 0 else "Horizontalmente"
            self.lbl_status_distorcao.setText(f"⚠️ ALERTA: Imagem {tipo}\n{eixo} ({desvio_percentual:.1f}%)")
            self.lbl_status_distorcao.setStyleSheet("color: #D32F2F; font-weight: bold;")

        paper_w_cm, paper_h_cm = self.get_paper_size_cm()
        pixel_per_cm_x = pixmap_w / target_w_cm
        pixel_per_cm_y = pixmap_h / target_h_cm

        cut_w_px = paper_w_cm * pixel_per_cm_x
        cut_h_px = paper_h_cm * pixel_per_cm_y

        pen = QPen(QColor(0, 255, 255, 200)) 
        pen.setWidth(max(2, int(pixmap_w * 0.005)))
        pen.setStyle(Qt.PenStyle.DashLine)

        for c in range(1, cols):
            x = c * cut_w_px
            if x < pixmap_w:
                self.scene.addLine(x, 0, x, pixmap_h, pen)
                
        for r in range(1, rows):
            y = r * cut_h_px
            if y < pixmap_h:
                self.scene.addLine(0, y, pixmap_w, y, pen)

        self.view.fitInView(QRectF(0, 0, pixmap_w, pixmap_h), Qt.AspectRatioMode.KeepAspectRatio)
        
        self.lbl_info.setText(f"Páginas necessárias: {cols * rows} ({cols}x{rows})\nTamanho final impresso: {target_w_cm:.1f} x {target_h_cm:.1f} cm")

    def process_image(self):
        if not self.image_path:
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Selecionar pasta para salvar as partes")
        if not save_dir:
            return

        self.btn_process.setText("Processando... Aguarde")
        self.btn_process.setEnabled(False)
        QApplication.processEvents()

        try:
            paper_w_cm, paper_h_cm = self.get_paper_size_cm()
            cols, rows, grid_w_cm, grid_h_cm, target_w_cm, target_h_cm = self.calculate_grid()

            target_w_px = int((target_w_cm / 2.54) * self.dpi)
            target_h_px = int((target_h_cm / 2.54) * self.dpi)
            
            paper_w_px = int((paper_w_cm / 2.54) * self.dpi)
            paper_h_px = int((paper_h_cm / 2.54) * self.dpi)

            img = Image.open(self.image_path)
            img_resized = img.resize((target_w_px, target_h_px), Image.Resampling.LANCZOS)
            
            part_number = 1
            for r in range(rows):
                for c in range(cols):
                    left = c * paper_w_px
                    upper = r * paper_h_px
                    right = left + paper_w_px
                    lower = upper + paper_h_px
                    
                    box = (left, upper, right, lower)
                    part = img_resized.crop(box)
                    
                    if part.mode in ('RGBA', 'P'):
                        part = part.convert('RGB')
                        
                    filename = os.path.join(save_dir, f"parte_{part_number:03d}_linha{r+1}_col{c+1}.jpg")
                    part.save(filename, "JPEG", quality=95)
                    part_number += 1
            
            QMessageBox.information(self, "Sucesso", f"Processamento concluído!\nAs {cols*rows} partes foram salvas em:\n{save_dir}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento:\n{str(e)}")
        
        finally:
            self.btn_process.setText("Processar e Salvar Recortes")
            self.btn_process.setEnabled(True)

# =====================================================================
# 4. EXECUÇÃO PRINCIPAL DO APLICATIVO
# =====================================================================
if __name__ == '__main__':
    # Configuração para o Windows exibir o ícone correto na barra de tarefas
    if sys.platform == 'win32':
        myappid = 'raposotech.mosaico.app.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    
    # Define o ícone global (precisa existir o arquivo icone.png na mesma pasta)
    app.setWindowIcon(QIcon("icone.png"))
    
    # 1. Validação da Licença via API
    ativador = TelaAtivacao()
    if not ativador.verificar_licenca_existente():
        resultado = ativador.exec()
        if resultado != QDialog.DialogCode.Accepted:
            sys.exit() # Encerra se o usuário cancelar a ativação
    
    # 2. Inicia o Splash Screen e o Programa Principal
    janela_principal = MosaicoApp()
    splash = SplashScreen(janela_principal)
    splash.show()
    
    sys.exit(app.exec())    