import { useState } from 'react';
import './login.css';

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <span className="brand-mark-cross">+</span>
    </span>
  );
}

function Login({ onCreateAccount, onLogin }) {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setError('');
    setIsSubmitting(true);
    try {
      await onLogin(formData.get('email'), formData.get('password'), rememberMe);
    } catch (submissionError) {
      setError(submissionError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-visual" aria-label="Présentation de MediCore AI">
        <div className="visual-glow visual-glow-one" />
        <div className="visual-glow visual-glow-two" />

        <div className="visual-content">
          <div className="brand brand-light">
            <BrandMark />
            <span>MediCore <strong>AI</strong></span>
          </div>

          <div className="visual-copy">
            <p className="eyebrow">Laboratoire médical intelligent</p>
            <h1>La précision médicale, <em>augmentée par l’IA.</em></h1>
            <p className="visual-description">
              Centralisez vos analyses, accélérez vos diagnostics et prenez de
              meilleures décisions, en toute confiance.
            </p>
          </div>

          <div className="trust-card">
            <div className="trust-icon" aria-hidden="true">
              <span>✓</span>
            </div>
            <div>
              <strong>Vos données sont protégées</strong>
              <span>Connexion sécurisée et conforme aux normes de santé</span>
            </div>
          </div>
        </div>

        <p className="visual-footer">© 2024 MediCore AI · L’innovation au service du soin</p>
      </section>

      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-form-container">
          <div className="brand brand-dark">
            <BrandMark />
            <span>MediCore <strong>AI</strong></span>
          </div>

          <div className="form-heading">
            <p className="eyebrow">Bienvenue</p>
            <h2 id="login-title">Connectez-vous à votre espace</h2>
            <p>Accédez à vos analyses et à vos outils de diagnostic.</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="email">Adresse e-mail</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="5" width="18" height="14" rx="2" />
                    <path d="m3 7 9 6 9-6" />
                  </svg>
                </span>
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="vous@exemple.com"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="field-group">
              <div className="label-row">
                <label htmlFor="password">Mot de passe</label>
                <a href="#forgot-password">Mot de passe oublié ?</a>
              </div>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none">
                    <rect x="4" y="10" width="16" height="11" rx="2" />
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                    <path d="M12 14v3" />
                  </svg>
                </span>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Entrez votre mot de passe"
                  autoComplete="current-password"
                  required
                />
                <button
                  className="password-toggle"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                >
                  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    {showPassword ? (
                      <>
                        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                        <circle cx="12" cy="12" r="3" />
                      </>
                    ) : (
                      <>
                        <path d="m3 3 18 18" />
                        <path d="M10.6 5.2A9.8 9.8 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-3.1 3.9M6.2 6.2C3.5 8.1 2 12 2 12s3.5 7 10 7a9.8 9.8 0 0 0 3.4-.6" />
                      </>
                    )}
                  </svg>
                </button>
              </div>
            </div>

            <label className="remember-option">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(event) => setRememberMe(event.target.checked)}
              />
              <span className="custom-checkbox" aria-hidden="true">✓</span>
              <span>Se souvenir de moi</span>
            </label>

            <button className="submit-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Connexion...' : 'Se connecter'}
              <span aria-hidden="true">→</span>
            </button>
          </form>
          {error && <p className="form-error" role="alert">{error}</p>}

          <p className="signup-prompt">
            Vous n’avez pas encore de compte ?             <button className="text-link-button" type="button" onClick={onCreateAccount}>
              Créer un compte
            </button>
          </p>

          <p className="help-text">
            Besoin d’aide ? <a href="#support">Contacter le support</a>
          </p>
        </div>
      </section>
    </main>
  );
}

export default Login;