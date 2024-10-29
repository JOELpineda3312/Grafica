import fitz  # PyMuPDF
import cv2
import numpy as np
from pyzbar .pyzbar import decode
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from datetime import datetime
import io  # Importar el módulo ios
from PIL import Image

class LetterRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Letter Renamer")
        self.root.geometry("800x600")
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Frame for controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Select folder button
        self.select_btn = ttk.Button(control_frame, text="Seleccionar Carpeta con PDFs", command=self.select_folder)
        self.select_btn.pack(side='left', padx=5)
        
        # Process button
        self.process_btn = ttk.Button(control_frame, text="Procesar Cartas", command=self.process_letters)
        self.process_btn.pack(side='left', padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=5)
        
        # Status text
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.status_text = tk.Text(self.status_frame, height=15, width=50)
        self.status_text.pack(fill='both', expand=True)
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(self.status_text)
        scrollbar.pack(side='right', fill='y')
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)
        
    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"Carpeta seleccionada: {self.folder_path}\n")
            
    def update_progress(self, current, total):
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.root.update()

    def try_decode_qr(self, image):
        # Attempt to decode the QR code
        decoded_objects = decode(image)
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
        return None
            
    def extract_qr_from_pdf(self, pdf_path):
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            page = pdf_document[0]
            
            # Convert page to image at high resolution
            zoom_matrix = fitz.Matrix(300/72, 300/72)  # 300 DPI
            pix = page.get_pixmap(matrix=zoom_matrix)
            
            # Convert to format that OpenCV can read
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Crop the upper center part of the image
            height, width = opencv_img.shape[:2]
            center_top_crop = opencv_img[0:int(height * 0.15), int(width * 0.4):int(width * 0.6)]  # Top 15% y centrado
            
            # Try to decode QR from the cropped image
            qr_code = self.try_decode_qr(center_top_crop)
            
            pdf_document.close()
            return qr_code
            
        except Exception as e:
            self.status_text.insert(tk.END, f"Error al procesar PDF {os.path.basename(pdf_path)}: {str(e)}\n")
            return None
            
    def process_letters(self):
        if not hasattr(self, 'folder_path'):
            messagebox.showerror("Error", "¡Por favor selecciona una carpeta primero!")
            return
            
        try:
            files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.pdf')]
            total_files = len(files)
            
            if total_files == 0:
                messagebox.showwarning("Advertencia", "No se encontraron archivos PDF en la carpeta seleccionada")
                return
                
            current_date = datetime.now().strftime("-20%y%m%d")
            processed_count = 0
            success_count = 0
            error_count = 0
            
            for index, file in enumerate(files):
                self.status_text.insert(tk.END, f"\nProcesando {file}...\n")
                self.status_text.see(tk.END)
                self.update_progress(index, total_files)
                
                pdf_path = os.path.join(self.folder_path, file)
                
                try :
                    qr_code = self.extract_qr_from_pdf(pdf_path)
                    
                    if qr_code:
                        # Create new filename
                        new_filename = f"{qr_code}{current_date}_0678.pdf"
                        new_path = os.path.join(self.folder_path, new_filename)
                        
                        # Rename file
                        os.rename(pdf_path, new_path)
                        self.status_text.insert(tk.END, f"✓ Renombrado a: {new_filename}\n")
                        success_count += 1
                    else:
                        self.status_text.insert(tk.END, f"✗ No se encontró código QR en {file}\n")
                        error_count += 1
                    
                except Exception as e:
                    self.status_text.insert(tk.END, f"✗ Error procesando {file}: {str(e)}\n")
                    error_count += 1
                    continue
                
                processed_count += 1
                
            self.update_progress(total_files, total_files)
            
            # Final summary
            summary = f"\n=== Resumen del Procesamiento ===\n"
            summary += f"Total de archivos: {total_files}\n"
            summary += f"Procesados exitosamente: {success_count}\n"
            summary += f"Errores: {error_count}\n"
            
            self.status_text.insert(tk.END, summary)
            self.status_text.see(tk.END)
            
            messagebox.showinfo("Proceso Completado", 
                              f"Procesamiento finalizado\n\n"
                              f"Exitosos: {success_count}\n"
                              f"Errores: {error_count}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error general: {str(e)}")
            
def main():
    root = tk.Tk()
    app = LetterRenamerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()