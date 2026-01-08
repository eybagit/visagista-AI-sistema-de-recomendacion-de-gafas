import React from "react";

/**
 * Formulario de datos del usuario para análisis de monturas
 * Componente TONTO: recibe datos y emite cambios via props
 */
const UserDataForm = ({ userData, onDataChange, onSubmit, disabled }) => {

    const handleChange = (e) => {
        const { name, value } = e.target;
        onDataChange({ [name]: value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit();
    };

    return (
        <form className="user-data-form" onSubmit={handleSubmit}>
            <h3 className="form-title">📋 Completa tus Datos</h3>

            {/* SECCIÓN 1: Datos Biométricos */}
            <fieldset className="form-section">
                <legend>Datos Biométricos</legend>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="genero">Género</label>
                        <select
                            id="genero"
                            name="genero"
                            value={userData.genero}
                            onChange={handleChange}
                            disabled={disabled}
                            required
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Hombre">Hombre</option>
                            <option value="Mujer">Mujer</option>
                            <option value="No Binario">No Binario</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="edad">Edad</label>
                        <input
                            type="number"
                            id="edad"
                            name="edad"
                            value={userData.edad}
                            onChange={handleChange}
                            placeholder="Ej: 28"
                            min="1"
                            max="120"
                            disabled={disabled}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="estatura">Estatura</label>
                        <input
                            type="text"
                            id="estatura"
                            name="estatura"
                            value={userData.estatura}
                            onChange={handleChange}
                            placeholder="Ej: 1.75m"
                            disabled={disabled}
                        />
                    </div>
                </div>
            </fieldset>

            {/* SECCIÓN 2: Auto-percepción de Rasgos */}
            <fieldset className="form-section">
                <legend>Auto-percepción de Rasgos</legend>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="formaMandibula">Forma de Mandíbula</label>
                        <select
                            id="formaMandibula"
                            name="formaMandibula"
                            value={userData.formaMandibula}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Angular/Marcada">Angular/Marcada</option>
                            <option value="Curva/Suave">Curva/Suave</option>
                            <option value="Puntiaguda">Puntiaguda</option>
                            <option value="Ancha en la base">Ancha en la base</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="frente">Frente</label>
                        <select
                            id="frente"
                            name="frente"
                            value={userData.frente}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Amplia/Alta">Amplia/Alta</option>
                            <option value="Estrecha/Baja">Estrecha/Baja</option>
                            <option value="Promedio">Promedio</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="narizPuente">Nariz/Puente</label>
                        <select
                            id="narizPuente"
                            name="narizPuente"
                            value={userData.narizPuente}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Tabique alto/Aguileño">Tabique alto/Aguileño</option>
                            <option value="Tabique plano/bajo">Tabique plano/bajo</option>
                            <option value="Ancho en la base">Ancho en la base</option>
                            <option value="Fino/Estrecho">Fino/Estrecho</option>
                        </select>
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="tonoPiel">Tono de Piel</label>
                        <select
                            id="tonoPiel"
                            name="tonoPiel"
                            value={userData.tonoPiel}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Clara (subtono frío)">Clara (subtono frío)</option>
                            <option value="Clara (subtono cálido)">Clara (subtono cálido)</option>
                            <option value="Media/Trigueña (subtono frío)">Media/Trigueña (subtono frío)</option>
                            <option value="Media/Trigueña (subtono cálido)">Media/Trigueña (subtono cálido)</option>
                            <option value="Oscura (subtono frío)">Oscura (subtono frío)</option>
                            <option value="Oscura (subtono cálido)">Oscura (subtono cálido)</option>
                            <option value="Neutra">Neutra</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="colorCabello">Color de Cabello</label>
                        <input
                            type="text"
                            id="colorCabello"
                            name="colorCabello"
                            value={userData.colorCabello}
                            onChange={handleChange}
                            placeholder="Ej: Negro, Castaño claro"
                            disabled={disabled}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="colorOjos">Color de Ojos</label>
                        <input
                            type="text"
                            id="colorOjos"
                            name="colorOjos"
                            value={userData.colorOjos}
                            onChange={handleChange}
                            placeholder="Ej: Marrón oscuro, Azul"
                            disabled={disabled}
                        />
                    </div>
                </div>
            </fieldset>

            {/* SECCIÓN 3: Uso y Estilo de Vida */}
            <fieldset className="form-section">
                <legend>Uso y Estilo de Vida</legend>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="usoPrincipal">Uso Principal</label>
                        <select
                            id="usoPrincipal"
                            name="usoPrincipal"
                            value={userData.usoPrincipal}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Lectura">Lectura</option>
                            <option value="Computadora todo el día">Computadora todo el día</option>
                            <option value="Conducir">Conducir</option>
                            <option value="Deporte">Deporte</option>
                            <option value="Moda/Estilo">Moda/Estilo</option>
                            <option value="Uso diario general">Uso diario general</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="estiloDeseado">Estilo Deseado</label>
                        <select
                            id="estiloDeseado"
                            name="estiloDeseado"
                            value={userData.estiloDeseado}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Minimalista">Minimalista</option>
                            <option value="Ejecutivo/Profesional">Ejecutivo/Profesional</option>
                            <option value="Creativo/Audaz">Creativo/Audaz</option>
                            <option value="Retro/Vintage">Retro/Vintage</option>
                            <option value="Invisible">Invisible</option>
                            <option value="Moderno">Moderno</option>
                            <option value="Casual">Casual</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="materialPreferido">Material Preferido</label>
                        <select
                            id="materialPreferido"
                            name="materialPreferido"
                            value={userData.materialPreferido}
                            onChange={handleChange}
                            disabled={disabled}
                        >
                            <option value="">Seleccionar...</option>
                            <option value="Metal">Metal</option>
                            <option value="Acetato/Plástico">Acetato/Plástico</option>
                            <option value="Combinado">Combinado (metal y plástico)</option>
                            <option value="Al aire">Al aire</option>
                            <option value="Indiferente">Indiferente</option>
                        </select>
                    </div>
                </div>

                <div className="form-group full-width">
                    <label htmlFor="exclusiones">¿Algún color o tipo que NO quieras?</label>
                    <input
                        type="text"
                        id="exclusiones"
                        name="exclusiones"
                        value={userData.exclusiones}
                        onChange={handleChange}
                        placeholder="Ej: No quiero monturas rojas ni muy gruesas"
                        disabled={disabled}
                    />
                </div>
            </fieldset>

            <button
                type="submit"
                className="btn-analyze"
                disabled={disabled || !userData.genero || !userData.edad}
            >
                {disabled ? (
                    <>
                        <span className="spinner"></span>
                        Analizando...
                    </>
                ) : (
                    '🔍 Analizar y Recomendar Monturas'
                )}
            </button>
        </form>
    );
};

export default UserDataForm;
