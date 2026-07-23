import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Cpu, ArrowRight, Lock, Mail, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('analyst@pmsengine.com');
  const [password, setPassword] = useState('••••••••••••');
  const [isRegister, setIsRegister] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    login({ email });
    navigate('/workspace');
  };

  return (
    <div className="login-page-container">
      {/* Left Visual Panel */}
      <div className="login-visual-panel">
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <Cpu size={20} />
          </div>
          <span style={{ fontSize: '1.2rem', fontWeight: '800', color: '#fff' }}>
            PMS <span className="gradient-text">ENGINE</span>
          </span>
        </Link>

        <div>
          <h2 style={{ fontSize: '2.5rem', fontWeight: '800', lineHeight: 1.2, marginBottom: '16px' }}>
            Institutional Quantitative <br />
            <span className="gradient-text">Research Infrastructure</span>
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.05rem', maxWidth: '480px', lineHeight: 1.6 }}>
            Access point-in-time market snapshots, ensemble ML predictions, risk analytics, and factor backtesting tools.
          </p>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={16} style={{ color: '#10b981' }} />
          <span>SOC-2 & Point-in-Time Historical Audit Compliance Guaranteed</span>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="login-form-panel">
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '1.8rem', fontWeight: '800', marginBottom: '8px' }}>
            {isRegister ? 'Create Workspace Account' : 'Sign in to Platform'}
          </h3>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
            {isRegister ? 'Enter your details to request research platform credentials.' : 'Enter your credentials to access your research workspace.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Work Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 40px',
                  background: 'var(--color-bg-input)',
                  border: '1px solid var(--color-border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--color-text-primary)',
                  outline: 'none',
                  fontSize: '0.9rem'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 40px',
                  background: 'var(--color-bg-input)',
                  border: '1px solid var(--color-border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--color-text-primary)',
                  outline: 'none',
                  fontSize: '0.9rem'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            style={{
              padding: '14px',
              background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.95rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '8px',
              boxShadow: '0 4px 20px rgba(99, 102, 241, 0.3)'
            }}
          >
            {isRegister ? 'Register Account' : 'Sign In to Workspace'} <ArrowRight size={18} />
          </button>
        </form>

        {/* SSO Future Proof Section */}
        <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid var(--color-border-subtle)', textAlign: 'center' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginBottom: '16px' }}>
            Or sign in with Institutional SSO
          </div>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button style={{ padding: '8px 16px', background: 'var(--color-bg-input)', border: '1px solid var(--color-border-subtle)', borderRadius: '4px', color: 'var(--color-text-secondary)', fontSize: '0.8rem', cursor: 'pointer' }}>
              Google SSO
            </button>
            <button style={{ padding: '8px 16px', background: 'var(--color-bg-input)', border: '1px solid var(--color-border-subtle)', borderRadius: '4px', color: 'var(--color-text-secondary)', fontSize: '0.8rem', cursor: 'pointer' }}>
              Microsoft Azure
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
