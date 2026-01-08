export const initialStore = () => {
  return {
    message: null,
    todos: [
      {
        id: 1,
        title: "Make the bed",
        background: null,
      },
      {
        id: 2,
        title: "Do my homework",
        background: null,
      }
    ],
    // === ANÁLISIS DE MONTURAS ===
    glassesAnalysis: {
      selfiePreview: null,    // Preview local de la imagen
      selfieUrl: null,        // URL de Cloudinary
      userData: {
        genero: '',
        edad: '',
        estatura: '',
        formaMandibula: '',
        frente: '',
        narizPuente: '',
        tonoPiel: '',
        colorCabello: '',
        colorOjos: '',
        usoPrincipal: '',
        estiloDeseado: '',
        materialPreferido: '',
        exclusiones: ''
      },
      recommendations: [],    // Imágenes con monturas generadas
      analysis: '',           // Texto de análisis
      loading: false,
      error: null,
      step: 1,                 // 1: Upload, 2: Formulario, 3: Resultados
      progress: 0,             // Progreso 0-100
      progressStatus: '',      // Mensaje de estado del progreso
      usage: null              // Costos de tokens de la transacción
    }
  }
}

export default function storeReducer(store, action = {}) {
  switch (action.type) {
    case 'set_hello':
      return {
        ...store,
        message: action.payload
      };

    case 'add_task':
      const { id, color } = action.payload
      return {
        ...store,
        todos: store.todos.map((todo) => (todo.id === id ? { ...todo, background: color } : todo))
      };

    // === GLASSES ANALYSIS ACTIONS ===
    case 'SET_SELFIE_PREVIEW':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          selfiePreview: action.payload
        }
      };

    case 'SET_USER_DATA':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          userData: { ...store.glassesAnalysis.userData, ...action.payload }
        }
      };

    case 'SET_STEP':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          step: action.payload
        }
      };

    case 'ANALYZE_START':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          loading: true,
          error: null,
          progress: 0,
          progressStatus: 'Iniciando...'
        }
      };

    case 'UPDATE_PROGRESS':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          progress: action.payload.progress,
          progressStatus: action.payload.status
        }
      };

    // Nuevos casos para carga progresiva
    case 'SET_SELFIE_URL':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          selfieUrl: action.payload,
          step: 2  // Mostrar resultados parciales
        }
      };

    case 'SET_ANALYSIS':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          analysis: action.payload
        }
      };

    case 'ADD_IMAGE':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          recommendations: [...store.glassesAnalysis.recommendations, action.payload]
        }
      };

    case 'SET_USAGE':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          usage: action.payload
        }
      };

    case 'ANALYZE_SUCCESS':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          loading: false,
          step: 2
        }
      };

    case 'ANALYZE_ERROR':
      return {
        ...store,
        glassesAnalysis: {
          ...store.glassesAnalysis,
          loading: false,
          error: action.payload
        }
      };

    case 'RESET_ANALYSIS':
      return {
        ...store,
        glassesAnalysis: {
          selfiePreview: null,
          selfieUrl: null,
          userData: {
            genero: '',
            edad: '',
            estatura: '',
            formaMandibula: '',
            frente: '',
            narizPuente: '',
            tonoPiel: '',
            colorCabello: '',
            colorOjos: '',
            usoPrincipal: '',
            estiloDeseado: '',
            materialPreferido: '',
            exclusiones: ''
          },
          recommendations: [],
          analysis: '',
          loading: false,
          error: null,
          step: 1
        }
      };

    default:
      return store;
  }
}

// === ACCIONES CENTRALIZADAS ===
export const glassesActions = {
  setSelfiePreview: (dispatch, imageData) => {
    dispatch({ type: 'SET_SELFIE_PREVIEW', payload: imageData });
  },

  setUserData: (dispatch, data) => {
    dispatch({ type: 'SET_USER_DATA', payload: data });
  },

  setStep: (dispatch, step) => {
    dispatch({ type: 'SET_STEP', payload: step });
  },

  analyzeface: async (dispatch, imageData, userData) => {
    dispatch({ type: 'ANALYZE_START' });

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL;

      // Usar streaming SSE para recibir datos progresivamente
      const response = await fetch(`${backendUrl}/api/analyze-face`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image: imageData,
          userData: userData
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error en el análisis');
      }

      // Leer el stream SSE
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Procesar líneas SSE completas
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Guardar línea incompleta
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              // Procesar cada tipo de mensaje
              switch (data.type) {
                case 'progress':
                  dispatch({ 
                    type: 'UPDATE_PROGRESS', 
                    payload: { progress: data.progress, status: data.status } 
                  });
                  break;
                  
                case 'selfie':
                  dispatch({ type: 'SET_SELFIE_URL', payload: data.selfie_url });
                  break;
                  
                case 'analysis':
                  dispatch({ type: 'SET_ANALYSIS', payload: data.analysis });
                  break;
                  
                case 'image':
                  dispatch({ type: 'ADD_IMAGE', payload: data.image });
                  break;
                  
                case 'usage':
                  dispatch({ type: 'SET_USAGE', payload: data.usage });
                  break;
                  
                case 'complete':
                  dispatch({ type: 'ANALYZE_SUCCESS', payload: {} });
                  break;
                  
                case 'error':
                case 'analysis_error':
                case 'images_error':
                  console.warn('[SSE] Error parcial:', data.error);
                  break;
              }
            } catch (e) {
              console.warn('[SSE] Error parsing:', e);
            }
          }
        }
      }

    } catch (error) {
      console.error('[SSE] Error:', error);
      dispatch({ type: 'ANALYZE_ERROR', payload: error.message });
      throw error;
    }
  },

  reset: (dispatch) => {
    dispatch({ type: 'RESET_ANALYSIS' });
  }
};

