import React, { useState } from "react";

/**
 * Componente para mostrar resultados del análisis con carga progresiva
 * Muestra secciones a medida que llegan los datos con sticky countdown
 */
const GlassesResults = ({
    recommendations,
    analysis,
    selfieUrl,
    onReset,
    imagesError,
    usage,
    loading,
    progress,
    progressStatus,
    timeRemaining,
    formatTime
}) => {
    // Estado para controlar rotación de cada imagen (en grados)
    // Usamos un Map con ID único de imagen como key
    const [imageRotations, setImageRotations] = useState({});

    // Función para rotar una imagen 90 grados
    const rotateImage = (imageId) => {
        setImageRotations(prev => ({
            ...prev,
            [imageId]: ((prev[imageId] || 0) + 90) % 360
        }));
    };

    // Calcular imágenes cargadas
    const imagesLoaded = recommendations?.length || 0;
    const totalImages = 4;

    // Skeleton/Loading para análisis
    const AnalysisSkeleton = () => (
        <div className="analysis-section loading-section">
            <h3 className="analysis-title">📊 Análisis Detallado</h3>
            <div className="loading-skeleton">
                <div className="skeleton-line"></div>
                <div className="skeleton-line short"></div>
                <div className="skeleton-line"></div>
                <div className="skeleton-line medium"></div>
                <p className="loading-text">Analizando tu rostro con IA...</p>
            </div>
        </div>
    );

    // Skeleton/Loading para imágenes
    const ImagesSkeleton = () => (
        <div className="frames-container loading-section">
            <div className="loading-skeleton images-skeleton">
                <div className="skeleton-image"></div>
                <div className="skeleton-image"></div>
                <p className="loading-text">Generando monturas personalizadas...</p>
            </div>
        </div>
    );

    return (
        <div className="glasses-results">
            {/* Sticky Countdown - Visible mientras carga */}
            {loading && (
                <div className="sticky-countdown">
                    <div className="countdown-content">
                        <div className="countdown-timer-inline">
                            <span className="countdown-icon">⏱️</span>
                            <span className="countdown-time">{formatTime ? formatTime(timeRemaining) : '0:00'}</span>
                        </div>
                        <div className="countdown-details">
                            <span className="images-count">📸 {imagesLoaded}/{totalImages} imágenes</span>
                            <span className="progress-text">{progressStatus || 'Procesando...'}</span>
                        </div>
                        <div className="mini-progress-bar">
                            <div
                                className="mini-progress-fill"
                                style={{ width: `${progress || 0}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            )}

            <h2 className="results-title">
                {loading ? '⏳ Procesando...' : '🎉 ¡Tus Monturas Recomendadas!'}
            </h2>

            {/* Sección de Costos - Solo mostrar cuando esté completo */}
            {usage && (
                <div className="usage-section">
                    <h3 className="usage-title">💰 Costo de la Transacción</h3>
                    <div className="usage-grid">
                        <div className="usage-item">
                            <span className="usage-label">Tokens de Entrada</span>
                            <span className="usage-value">{usage.prompt_tokens?.toLocaleString() || 0}</span>
                        </div>
                        <div className="usage-item">
                            <span className="usage-label">Tokens de Salida</span>
                            <span className="usage-value">{usage.output_tokens?.toLocaleString() || 0}</span>
                        </div>
                        <div className="usage-item">
                            <span className="usage-label">Tokens Totales</span>
                            <span className="usage-value usage-highlight">{usage.total_tokens?.toLocaleString() || 0}</span>
                        </div>
                        <div className="usage-item">
                            <span className="usage-label">Imágenes</span>
                            <span className="usage-value">{usage.image_generations || 0}/4</span>
                        </div>
                        <div className="usage-item">
                            <span className="usage-label">Análisis</span>
                            <span className="usage-value">{usage.text_generations ? '✓' : '✗'}</span>
                        </div>
                        <div className="usage-item">
                            <span className="usage-label">Tiempo</span>
                            <span className="usage-value">{usage.processing_time_seconds || 0}s</span>
                        </div>
                    </div>

                    {/* Costo estimado en USD */}
                    <div className="cost-summary">
                        <div className="cost-breakdown">
                            <span className="cost-label">💵 Costo Estimado Total:</span>
                            <span className="cost-value">
                                ${(() => {
                                    // Precios Gemini 2.5 Flash (por millón de tokens)
                                    const INPUT_PRICE_PER_M = 0.30;   // $0.30/M tokens entrada
                                    const OUTPUT_PRICE_PER_M = 2.50;  // $2.50/M tokens salida
                                    const IMAGE_COST = 0.039;         // $0.039 por imagen (1024x1024)

                                    const inputCost = ((usage.prompt_tokens || 0) / 1000000) * INPUT_PRICE_PER_M;
                                    const outputCost = ((usage.output_tokens || 0) / 1000000) * OUTPUT_PRICE_PER_M;
                                    const imageCost = (usage.image_generations || 0) * IMAGE_COST;

                                    const totalCost = inputCost + outputCost + imageCost;
                                    return totalCost.toFixed(4);
                                })()}
                            </span>
                            <span className="cost-currency">USD</span>
                        </div>
                        <p className="cost-note">
                            * Basado en precios de Gemini 2.5 Flash: $0.30/M entrada, $2.50/M salida, $0.039/imagen
                        </p>
                    </div>
                </div>
            )}

            {/* Análisis de texto - Mostrar cuando llegue o skeleton si está cargando */}
            {analysis ? (
                <div className="analysis-section">
                    <h3 className="analysis-title">📊 Análisis Detallado</h3>
                    <div className="analysis-content">
                        {analysis.split('\n').map((paragraph, idx) => {
                            if (paragraph.startsWith('###')) {
                                return <h4 key={idx} className="analysis-h4">{paragraph.replace('###', '').trim()}</h4>;
                            } else if (paragraph.startsWith('##')) {
                                return <h3 key={idx} className="analysis-h3">{paragraph.replace('##', '').trim()}</h3>;
                            } else if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
                                return <p key={idx} className="analysis-bold">{paragraph.replace(/\*\*/g, '')}</p>;
                            } else if (paragraph.startsWith('-')) {
                                return <li key={idx} className="analysis-list-item">{paragraph.substring(1).trim()}</li>;
                            } else if (paragraph.trim()) {
                                return <p key={idx} className="analysis-paragraph">{paragraph}</p>;
                            }
                            return null;
                        })}
                    </div>
                </div>
            ) : loading && (
                <AnalysisSkeleton />
            )}

            {/* Imágenes - Agrupar por montura y mostrar on_face + product */}
            {recommendations && recommendations.length > 0 ? (
                <div className="frames-container">
                    {(() => {
                        // Agrupar imágenes por estilo de montura
                        const frameGroups = {};
                        recommendations.forEach(img => {
                            const frameId = img.style || 'unknown';
                            if (!frameGroups[frameId]) {
                                frameGroups[frameId] = {
                                    name: img.frame_name || 'Montura',
                                    description: img.description || '',
                                    on_face: null,
                                    product: null
                                };
                            }
                            if (img.type === 'on_face') {
                                frameGroups[frameId].on_face = img;
                            } else if (img.type === 'product') {
                                frameGroups[frameId].product = img;
                            }
                        });

                        return Object.entries(frameGroups).map(([frameId, group], idx) => (
                            <div key={frameId} className="frame-group">
                                <div className="frame-header">
                                    <span className="frame-number">Opción {idx + 1}</span>
                                    <h3 className="frame-name">{group.name}</h3>
                                </div>

                                <div className="frame-images">
                                    {/* Imagen en rostro */}
                                    {group.on_face && (
                                        <div className="frame-image-card">
                                            <div className="image-type-label">📸 En tu rostro</div>
                                            <div className="image-wrapper">
                                                <img
                                                    src={group.on_face.data}
                                                    alt={`${group.name} en rostro`}
                                                    className="generated-image"
                                                    style={{
                                                        transform: `rotate(${imageRotations[`${frameId}_on_face`] || 0}deg)`,
                                                        transition: 'transform 0.3s ease'
                                                    }}
                                                />
                                            </div>
                                            <button
                                                className="btn-rotate-image"
                                                onClick={() => rotateImage(`${frameId}_on_face`)}
                                                title="Rotar imagen 90°"
                                            >
                                                🔄 Rotar
                                            </button>
                                        </div>
                                    )}

                                    {/* Imagen del producto */}
                                    {group.product && (
                                        <div className="frame-image-card">
                                            <div className="image-type-label">👓 Montura sola</div>
                                            <div className="image-wrapper">
                                                <img
                                                    src={group.product.data}
                                                    alt={`${group.name} producto`}
                                                    className="generated-image"
                                                    style={{
                                                        transform: `rotate(${imageRotations[`${frameId}_product`] || 0}deg)`,
                                                        transition: 'transform 0.3s ease'
                                                    }}
                                                />
                                            </div>
                                            <button
                                                className="btn-rotate-image"
                                                onClick={() => rotateImage(`${frameId}_product`)}
                                                title="Rotar imagen 90°"
                                            >
                                                🔄 Rotar
                                            </button>
                                        </div>
                                    )}
                                </div>

                                {/* Descripción de la montura */}
                                {group.description && (
                                    <div className="frame-description">
                                        <p>{group.description}</p>
                                    </div>
                                )}
                            </div>
                        ));
                    })()}

                    {/* Mostrar skeleton para imágenes pendientes */}
                    {loading && recommendations.length < 4 && (
                        <div className="frame-group loading-card">
                            <div className="frame-header">
                                <span className="frame-number">Generando...</span>
                                <h3 className="frame-name">Procesando...</h3>
                            </div>
                            <div className="loading-skeleton">
                                <div className="skeleton-image"></div>
                                <p className="loading-text">Creando imagen con IA...</p>
                            </div>
                        </div>
                    )}
                </div>
            ) : loading && analysis ? (
                <ImagesSkeleton />
            ) : !loading && (
                <div className="images-error-section">
                    <div className="images-error-card">
                        <span className="error-icon">⚠️</span>
                        <h4>Las imágenes no pudieron generarse</h4>
                        {imagesError && <p className="error-details">{imagesError}</p>}
                        <p className="error-info">
                            El análisis de texto está disponible arriba.
                        </p>
                    </div>
                </div>
            )}

            {/* Selfie original */}
            {selfieUrl && (
                <div className="original-selfie">
                    <h4>Tu Selfie Original</h4>
                    <img src={selfieUrl} alt="Selfie original" className="selfie-thumbnail" />
                </div>
            )}

            {/* Botón para nuevo análisis */}
            <div className="actions">
                <button
                    type="button"
                    className="btn-new-analysis"
                    onClick={onReset}
                    disabled={loading}
                >
                    {loading ? '⏳ Procesando...' : '🔄 Realizar Nuevo Análisis'}
                </button>
            </div>
        </div>
    );
};

export default GlassesResults;
