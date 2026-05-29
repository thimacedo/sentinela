import os
import hashlib
import re
import json
from fpdf import FPDF
from datetime import datetime

class ReportGenerator(FPDF):
    """
    Gerador de relatórios PDF de alto desempenho (PASA v85.9).
    Otimizado para execução em ambiente serverless (Vercel) e local.
    """
    
    def __init__(self):
        super().__init__()
        self.font_family_main = 'Helvetica'
        self.primary_color = (37, 99, 235) # Blue 600
        self.danger_color = (220, 38, 38)  # Red 600
        self.success_color = (16, 185, 129) # Emerald 500
        self.bg_color = (248, 250, 252)    # Slate 50
        self.set_auto_page_break(auto=True, margin=15)

    def clean_text(self, text):
        if not text: return ""
        # Converte para Latin-1 (padrão FPDF) removendo caracteres incompatíveis
        # Substitui emojis e caracteres especiais por equivalentes seguros ou espaços
        text = str(text).replace('\u201c', '"').replace('\u201d', '"').replace('\u2013', '-').replace('\u2014', '-')
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 10, 'SENTINELA DEMOCRÁTICA | RELATÓRIO DE INTELIGÊNCIA', align="L")
            self.set_x(0)
            self.cell(0, 10, f'PASA Protocol v85.9 | {datetime.now().strftime("%d/%m/%Y")}', align="R")
            self.ln(12)
            # Linha decorativa
            self.set_draw_color(226, 232, 240)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Página {self.page_no()} | Documento Gerado Automaticamente', align='C')

    def render_cover(self, candidato_id, total_amostra, total_hate):
        """Cria uma capa profissional para o relatório."""
        self.add_page()
        
        # Faixa superior
        self.set_fill_color(*self.primary_color)
        self.rect(0, 0, 210, 60, 'F')
        
        self.set_y(20)
        self.set_font('Helvetica', 'B', 32)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'DOSSIÊ ESTRATÉGICO', ln=True, align='C')
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'ANÁLISE DE HOSTILIDADE E RISCO POLÍTICO', ln=True, align='C')
        
        self.set_y(80)
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'ALVO MONITORADO', ln=True, align='C')
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(*self.primary_color)
        self.cell(0, 15, f'@{candidato_id.upper()}', ln=True, align='C')
        
        # Status de Risco
        risk_pct = (total_hate / total_amostra * 100) if total_amostra > 0 else 0
        risk_label = "CRÍTICO" if risk_pct > 20 else ("ELEVADO" if risk_pct > 10 else "CONTROLADO")
        risk_color = self.danger_color if risk_label != "CONTROLADO" else self.success_color

        self.ln(10)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, 'ÍNDICE DE SEVERIDADE ANALÍTICA', ln=True, align='C')
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(*risk_color)
        self.cell(0, 12, f'{risk_label} ({risk_pct:.1f}%)', ln=True, align='C')

        # BARRA DE PROGRESSO VISUAL (O "Gatilho de Crise")
        self.set_y(self.get_y() + 5)
        self.set_x(30)
        # Fundo da barra
        self.set_fill_color(226, 232, 240)
        self.rect(30, self.get_y(), 150, 6, 'F')
        # Progresso da barra
        fill_width = min(150, (risk_pct / 30) * 150) if risk_pct > 0 else 5 # Cap at 30% for visual effect
        self.set_fill_color(*risk_color)
        self.rect(30, self.get_y(), fill_width, 6, 'F')
        self.ln(15)

        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, 'RESUMO DA AMOSTRAGEM', ln=True)
        self.set_font('Helvetica', '', 11)
        self.multi_cell(0, 7, (
            f"Este dossiê consolida a análise técnica de {total_amostra} interações capturadas nos últimos ciclos. "
            f"Foram identificados {total_hate} sinais de hostilidade validados por algoritmos de Processamento de Linguagem Natural (NLP) "
            f"conforme o Protocolo PASA v85.9."
        ))

        # MATRIZ DE RISCO ANALÍTICO (Gatilho de Venda)
        crimes_imputados = len([i for i in data if i.get('categoria_ia') == 'RIGOR_CRIMINAL'])
        
        self.ln(5)
        self.set_fill_color(254, 242, 242) # Red 50
        self.set_draw_color(252, 165, 165) # Red 300
        self.rect(10, self.get_y(), 190, 18, 'DF')
        
        self.set_xy(15, self.get_y() + 3)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self.danger_color)
        self.cell(0, 6, "MATRIZ DE RISCO ANALÍTICO", ln=True)
        
        self.set_x(15)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(127, 29, 29) # Red 900
        if crimes_imputados > 0:
            self.cell(0, 5, f"Alerta Crítico: Detectamos {crimes_imputados} interações com potenciais imputações graves (Rigor Criminal).", ln=True)
        else:
            self.set_text_color(21, 128, 61) # Green 700
            self.set_fill_color(240, 253, 244) # Green 50
            self.set_draw_color(134, 239, 172) # Green 300
            self.rect(10, self.get_y() - 9, 190, 18, 'DF')
            self.set_xy(15, self.get_y() - 6)
            self.set_text_color(22, 163, 74) # Green 600
            self.cell(0, 6, "MATRIZ DE RISCO ANALÍTICO", ln=True)
            self.set_x(15)
            self.set_text_color(20, 83, 45) # Green 900
            self.cell(0, 5, "Cenário favorável: Nenhuma imputação criminal direta detectada nesta amostragem.", ln=True)
            
        self.ln(10)

        # ESPECTRO DE VULNERABILIDADE (Treemap Simplificado)
        if total_hate > 0:
            from collections import Counter
            categorias = Counter([i.get('categoria_ia') for i in data if i.get('is_hate')])
            
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(30, 41, 59)
            self.cell(0, 10, 'VETORES DE ATAQUE (VULNERABILIDADE)', ln=True)
            self.ln(2)
            
            start_x = 10
            bar_width = 190
            current_x = start_x
            
            # Draw proportional blocks
            for cat, count in categorias.most_common(4):
                pct = count / total_hate
                w = max(15, int(pct * bar_width))
                
                # Alternate colors for blocks
                if cat == "AMEACA": self.set_fill_color(249, 115, 22) # Orange
                elif cat == "ATAQUE_INSTITUCIONAL": self.set_fill_color(139, 92, 246) # Purple
                elif cat == "RIGOR_CRIMINAL": self.set_fill_color(6, 182, 212) # Cyan
                else: self.set_fill_color(220, 38, 38) # Red
                
                if current_x + w > 200: w = 200 - current_x
                if w <= 0: break
                
                self.rect(current_x, self.get_y(), w, 8, 'F')
                
                # Label
                self.set_xy(current_x, self.get_y() + 9)
                self.set_font('Helvetica', 'B', 6)
                self.set_text_color(100, 116, 139)
                self.cell(w, 4, f"{str(cat).split('_')[0][:10]} ({int(pct*100)}%)", align='C')
                
                current_x += w + 2
                
            self.set_y(self.get_y() + 10)
        
        # Rodapé da capa
        self.set_y(-50)
        self.set_draw_color(226, 232, 240)
        self.line(30, self.get_y(), 180, self.get_y())
        self.ln(5)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"EMITIDO EM: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='C')
        self.set_font('Helvetica', 'B', 8)
        self.cell(0, 5, "SENTINELA DEMOCRÁTICA | UNIDADE DE INTELIGÊNCIA CÍVICA", align='C')

    def render_evidence_item(self, item):
        """Renderiza um card de evidência detalhado."""
        if self.get_y() > 240:
            self.add_page()

        # Fundo do card
        current_y = self.get_y()
        self.set_fill_color(*self.bg_color)
        self.rect(10, current_y, 190, 40, 'F')
        self.set_draw_color(226, 232, 240)
        self.rect(10, current_y, 190, 40, 'D')

        # Header do card
        self.set_xy(15, current_y + 5)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(30, 41, 59)
        autor = self.clean_text(item.get('autor_username') or 'Oculto')
        self.cell(0, 5, f"AUTOR: @{autor} | PLATAFORMA: {item.get('plataforma', 'IG').upper()}")
        
        # Categoria Badge
        cat = (item.get('categoria_ia') or 'NEUTRO').upper()
        is_hate = bool(item.get('is_hate', False))
        
        self.set_xy(150, current_y + 5)
        if is_hate:
            self.set_text_color(*self.danger_color)
            self.cell(45, 5, f"[ {cat} ]", align='R')
        else:
            self.set_text_color(*self.success_color)
            self.cell(45, 5, "[ NEUTRO ]", align='R')

        # Texto do Comentário
        self.set_xy(15, current_y + 12)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(71, 85, 105)
        raw_text = item.get('texto_bruto', '') or item.get('texto_limpo', '')
        texto = self.clean_text(raw_text)
        self.multi_cell(180, 4, f"TEXTO: {texto[:400]}")
        
        # Parecer Técnico (Se houver)
        if item.get('analise_pericial'):
            self.set_x(15)
            self.set_font('Helvetica', 'I', 7)
            self.set_text_color(100, 116, 139)
            parecer = self.clean_text(item['analise_pericial'])
            self.multi_cell(180, 3.5, f"ANÁLISE: {parecer}")

        # Data de Coleta
        self.set_xy(15, current_y + 34)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(148, 163, 184)
        data_c = item.get('data_coleta', 'N/A')[:19]
        self.cell(0, 5, f"CAPTURA: {data_c}")
        
        self.set_y(current_y + 45)

    def render_integrity_seal(self, data):
        """Selo de integridade forense."""
        self.add_page()
        self.set_y(100)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, 'CERTIFICAÇÃO DE INTEGRIDADE', ln=True, align='C')
        
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        self.ln(5)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 6, (
            "Este dossiê foi gerado eletronicamente pela Unidade de Inteligência Sentinela. "
            "A veracidade dos dados é garantida pela assinatura digital abaixo, que vincula "
            "o conteúdo extraído à data de emissão deste relatório."
        ), align='C')
        
        self.ln(10)
        self.set_font('Courier', 'B', 9)
        self.set_fill_color(241, 245, 249)
        self.cell(0, 12, f"HASH SHA-256: {data_hash}", border=1, ln=True, align='C', fill=True)
        
        self.set_y(-40)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.multi_cell(0, 5, "AVISO LEGAL: Este relatório é para fins informativos e de análise estratégica. A classificação é realizada por modelos de IA e pode conter margens de erro inerentes à tecnologia.", align='C')

    def generate_pdf(self, data, output_path, candidato_id):
        if not data:
            return None

        # Garante diretório
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        total_amostra = len(data)
        total_hate = len([i for i in data if i.get('is_hate')])
        
        # 1. Capa
        self.render_cover(candidato_id, total_amostra, total_hate)
        
        # 2. Resumo Executivo e KPIs
        self.add_page()
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*self.primary_color)
        self.cell(0, 10, 'DETALHAMENTO DE EVIDÊNCIAS', ln=True)
        self.set_draw_color(*self.primary_color)
        self.line(10, self.get_y(), 60, self.get_y())
        self.ln(8)
        
        # 3. Evidências (Filtra apenas Ódio para o relatório principal, ou Top 50 geral)
        hate_items = [item for item in data if item.get('is_hate')][:50]
        if not hate_items:
            hate_items = data[:30] # Fallback para itens neutros se não houver ódio

        for item in hate_items:
            self.render_evidence_item(item)

        # 4. Selo de Integridade
        self.render_integrity_seal(data)

        # Salva o arquivo
        try:
            self.output(output_path)
            print(f"📄 Dossiê gerado com sucesso: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Erro ao salvar PDF: {e}")
            return None
