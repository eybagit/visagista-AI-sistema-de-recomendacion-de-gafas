import React from "react";

/**
 * Componente para subir selfie y lanzar análisis
 * Flujo simplificado: Sube foto → Analiza directamente con IA
 */
const SelfieUploader = ({ selfiePreview, onImageSelect, onAnalyze, disabled, loading }) => {

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validar que sea imagen
            if (!file.type.startsWith('image/')) {
                alert('Por favor selecciona una imagen válida');
                return;
            }

            // Convertir a base64
            const reader = new FileReader();
            reader.onloadend = () => {
                onImageSelect(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="selfie-uploader">
            <h3 className="uploader-title">
                📸 Sube tu Selfie
            </h3>

            <p className="uploader-instructions">
                La foto debe ser <strong>frontal</strong>, con buena iluminación,
                sin gafas puestas, sin gorras/sombreros y con el cabello retirado del rostro.
                <br /><br />
                <strong>🤖 La IA analizará automáticamente tu rostro</strong> y te recomendará
                las mejores monturas para ti.
            </p>

            <div className="upload-area">
                {selfiePreview ? (
                    <div className="preview-container">
                        <img
                            src={selfiePreview}
                            alt="Preview de selfie"
                            className="selfie-preview"
                        />
                        <div className="preview-actions">
                            <button
                                type="button"
                                className="btn-change-photo"
                                onClick={() => onImageSelect(null)}
                                disabled={disabled || loading}
                            >
                                📷 Cambiar foto
                            </button>
                            <button
                                type="button"
                                className="btn-analyze-main"
                                onClick={onAnalyze}
                                disabled={disabled || loading}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner"></span>
                                        Analizando...
                                    </>
                                ) : (
                                    '🔍 Analizar con IA'
                                )}
                            </button>
                        </div>
                    </div>
                ) : (
                    <label className="upload-label">
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            disabled={disabled}
                            className="file-input"
                        />
                        <div className="upload-placeholder">
                            <span className="upload-icon">📷</span>
                            <span className="upload-text">Haz clic para seleccionar tu selfie</span>
                            <span className="upload-hint">JPG, PNG o WEBP</span>
                        </div>
                    </label>
                )}
            </div>
        </div>
    );
};

export default SelfieUploader;

