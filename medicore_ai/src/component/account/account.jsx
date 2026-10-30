import { useState } from 'react';
import './account.css';

function Account({ onAccountCreated, onBackToLogin }) {
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    age: '',
    role: 'patient',
    telephone: '',
    email: '',
    password: '',
  });

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData((currentData) => ({ ...currentData, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    Promise.resolve(onAccountCreated({ ...formData, age: Number(formData.age) }))
      .catch((submissionError) => setError(submissionError.message))
      .finally(() => setIsSubmitting(false));
  }

  return (
    <main className="account-page">
      <div className="account-decoration account-decoration-one" />
      <div className="account-decoration account-decoration-two" />
      <section className="account-card" aria-labelledby="account-title">
        <button className="back-button" type="button" onClick={onBackToLogin}>
          <span aria-hidden="true">←</span> Retour à la connexion
        </button>
        <div className="account-brand">
          <span className="account-brand-mark" aria-hidden="true">+</span>
          <span>MediCore <strong>AI</strong></span>
        </div>
        <div className="account-heading">
          <p className="account-eyebrow">Nouveau membre</p>
          <h1 id="account-title">Créer votre compte</h1>
          <p>Rejoignez votre laboratoire médical intelligent.</p>
        </div>

        <form className="account-form" onSubmit={handleSubmit}>
          <div className="account-fields-row">
            <div className="account-field">
              <label htmlFor="prenom">Prénom</label>
              <input id="prenom" name="prenom" type="text" placeholder="Votre prénom" value={formData.prenom} onChange={handleChange} autoComplete="given-name" required />
            </div>
            <div className="account-field">
              <label htmlFor="nom">Nom</label>
              <input id="nom" name="nom" type="text" placeholder="Votre nom" value={formData.nom} onChange={handleChange} autoComplete="family-name" required />
            </div>
          </div>
          <div className="account-fields-row">
            <div className="account-field">
              <label htmlFor="age">Âge</label>
              <input id="age" name="age" type="number" min="1" max="120" placeholder="Votre âge" value={formData.age} onChange={handleChange} required />
            </div>
            <div className="account-field">
              <label htmlFor="telephone">Téléphone</label>
              <input id="telephone" name="telephone" type="tel" placeholder="+33 6 00 00 00 00" value={formData.telephone} onChange={handleChange} autoComplete="tel" required />
            </div>
          </div>
          <div className="account-field">
            <label htmlFor="role">Votre rôle</label>
            <select id="role" name="role" value={formData.role} onChange={handleChange}>
              <option value="patient">Patient</option>
              <option value="doctor">Docteur</option>
            </select>
          </div>
          <div className="account-field">
            <label htmlFor="email">Adresse e-mail</label>
            <input id="email" name="email" type="email" placeholder="vous@exemple.com" value={formData.email} onChange={handleChange} autoComplete="email" required />
          </div>
          <div className="account-field">
            <label htmlFor="password">Mot de passe</label>
            <input id="password" name="password" type="password" placeholder="8 caractères minimum" value={formData.password} onChange={handleChange} autoComplete="new-password" minLength="8" required />
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="account-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Création en cours...' : 'Créer mon compte'} <span aria-hidden="true">→</span>
          </button>
        </form>
        <p className="account-security">
          <span aria-hidden="true">✓</span> Vos informations restent confidentielles et sécurisées.
        </p>
      </section>
    </main>
  );
}

export default Account;