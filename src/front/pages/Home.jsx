import React, { useState, useEffect } from "react";
import useGlobalReducer from "../hooks/useGlobalReducer.jsx";
import { glassesActions } from "../store.js";
import SelfieUploader from "../components/SelfieUploader.jsx";
import GlassesResults from "../components/GlassesResults.jsx";

/**
 * Home - Página principal para recomendación de monturas con IA
 * Flujo simplificado: Selfie → Análisis automático → Resultados
 */
export const Home = () => {
	const { store, dispatch } = useGlobalReducer();
	const { glassesAnalysis } = store;

	// Estado para cuenta regresiva
	const [timeRemaining, setTimeRemaining] = useState(300); // 5 minutos = 300 segundos

	// === HANDLERS ===
	const handleImageSelect = (imageData) => {
		glassesActions.setSelfiePreview(dispatch, imageData);
	};

	const handleAnalyze = async () => {
		try {
			// Analizar directamente sin datos del usuario
			await glassesActions.analyzeface(
				dispatch,
				glassesAnalysis.selfiePreview,
				{} // Sin datos del usuario - Gemini analizará todo
			);
		} catch (error) {
			console.error("Error en análisis:", error);
		}
	};

	// Hook para manejar cuenta regresiva
	useEffect(() => {
		let interval;

		if (glassesAnalysis.loading) {
			// Reiniciar contador cuando empieza el loading
			setTimeRemaining(300);

			// Iniciar cuenta regresiva
			interval = setInterval(() => {
				setTimeRemaining(prev => {
					if (prev <= 0) return 0;
					return prev - 1;
				});
			}, 1000); // Actualizar cada segundo
		} else {
			// Limpiar intervalo cuando termina el loading
			if (interval) clearInterval(interval);
		}

		// Cleanup al desmontar
		return () => {
			if (interval) clearInterval(interval);
		};
	}, [glassesAnalysis.loading]);

	// Formatear tiempo como MM:SS
	const formatTime = (seconds) => {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	};

	const handleReset = () => {
		glassesActions.reset(dispatch);
	};

	// === RENDER ===
	return (
		<div className="glasses-analyzer-container">
			{/* Header */}
			<header className="analyzer-header">
				<h1 className="main-title">
					👓 Visagista Óptico IA
				</h1>
				<p className="subtitle">
					Sube tu selfie y nuestra IA analizará tu rostro para recomendarte las monturas perfectas
				</p>
			</header>

			{/* Progress Steps - Simplificado a 2 pasos */}
			<div className="progress-steps">
				<div className={`step ${glassesAnalysis.step >= 1 ? 'active' : ''} ${glassesAnalysis.step > 1 ? 'completed' : ''}`}>
					<span className="step-number">1</span>
					<span className="step-label">Selfie</span>
				</div>
				<div className="step-connector"></div>
				<div className={`step ${glassesAnalysis.step >= 2 ? 'active' : ''}`}>
					<span className="step-number">2</span>
					<span className="step-label">Resultados</span>
				</div>
			</div>

			{/* Error Display */}
			{glassesAnalysis.error && (
				<div className="error-alert">
					<span className="error-icon">⚠️</span>
					<span className="error-message">{glassesAnalysis.error}</span>
					<button onClick={() => dispatch({ type: 'ANALYZE_ERROR', payload: null })}>✕</button>
				</div>
			)}

			{/* Main Content */}
			<main className="analyzer-content">
				{/* Step 1: Upload Selfie + Analyze Button */}
				{glassesAnalysis.step === 1 && (
					<SelfieUploader
						selfiePreview={glassesAnalysis.selfiePreview}
						onImageSelect={handleImageSelect}
						onAnalyze={handleAnalyze}
						disabled={glassesAnalysis.loading}
						loading={glassesAnalysis.loading}
					/>
				)}

				{/* Step 2: Results */}
				{glassesAnalysis.step === 2 && (
					<GlassesResults
						recommendations={glassesAnalysis.recommendations}
						analysis={glassesAnalysis.analysis}
						selfieUrl={glassesAnalysis.selfieUrl}
						onReset={handleReset}
						imagesError={glassesAnalysis.imagesError}
						usage={glassesAnalysis.usage}
						loading={glassesAnalysis.loading}
						progress={glassesAnalysis.progress}
						progressStatus={glassesAnalysis.progressStatus}
						timeRemaining={timeRemaining}
						formatTime={formatTime}
					/>
				)}
			</main>

			{/* Loading Overlay - Solo en Step 1 para evitar superposición con resultados progresivos */}
			{glassesAnalysis.loading && glassesAnalysis.step === 1 && (
				<div className="loading-overlay">
					<div className="loading-content">
						<div className="loading-spinner"></div>
						<p className="loading-text">Analizando tu rostro con IA...</p>

						{/* Cuenta regresiva */}
						<div className="countdown-timer">
							<div className="countdown-value">{formatTime(timeRemaining)}</div>
							<div className="countdown-label">Tiempo estimado restante</div>
						</div>

						{/* Barra de progreso */}
						<div className="progress-container">
							<div className="progress-bar">
								<div
									className="progress-fill"
									style={{ width: `${glassesAnalysis.progress}%` }}
								></div>
							</div>
							<div className="progress-info">
								<span className="progress-percentage">{glassesAnalysis.progress}%</span>
								<span className="progress-status">{glassesAnalysis.progressStatus}</span>
							</div>
						</div>

						<p className="loading-subtext">La IA está analizando tus rasgos faciales y generando recomendaciones personalizadas</p>
					</div>
				</div>
			)}
		</div>
	);
};

