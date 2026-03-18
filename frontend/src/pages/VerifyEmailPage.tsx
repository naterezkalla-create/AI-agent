import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { AlertCircle, Mail, CheckCircle2 } from 'lucide-react';

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [error, setError] = useState('');
  const [isVerified, setIsVerified] = useState(false);
  const [verificationAttempted, setVerificationAttempted] = useState(false);

  // Verify email token on mount
  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setError('No verification token provided');
        setVerificationAttempted(true);
        return;
      }

      try {
        const response = await fetch('/api/auth/verify-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (response.ok) {
          setIsVerified(true);
          // Redirect to dashboard after 3 seconds
          setTimeout(() => {
            navigate('/');
          }, 3000);
        } else {
          setError(data.detail || 'Failed to verify email');
        }
      } catch (err) {
        setError('An error occurred. Please try again.');
        console.error(err);
      } finally {
        setVerificationAttempted(true);
      }
    };

    verifyEmail();
  }, [token, navigate]);

  if (isVerified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 px-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="mb-6 inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100">
              <CheckCircle2 className="w-8 h-8 text-green-600" />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Email Verified!
            </h2>

            <p className="text-gray-600 mb-6">
              Your email has been verified successfully.
              You can now access all features.
            </p>

            <p className="text-sm text-gray-500 mb-6">
              Redirecting to dashboard in 3 seconds...
            </p>

            <Link
              to="/"
              className="w-full inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!verificationAttempted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="text-white text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-600 border-t-white rounded-full mb-4"></div>
          <p>Verifying your email...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 px-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-6 inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mx-auto">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">
              Verification Failed
            </h2>

            <p className="text-gray-600 mb-6 text-center">
              {error}
            </p>

            <div className="space-y-3">
              <button
                onClick={async () => {
                  try {
                    const token = localStorage.getItem('token');
                    await fetch('/api/auth/resend-verification-email', {
                      method: 'POST',
                      headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                      },
                    });
                    alert('Verification email resent. Check your inbox.');
                  } catch (err) {
                    alert('Failed to resend verification email');
                  }
                }}
                className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <Mail className="w-4 h-4" />
                Resend Verification Email
              </button>
              
              <Link
                to="/login"
                className="w-full block px-4 py-2 text-center bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors"
              >
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="text-white text-center">
        <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-600 border-t-white rounded-full mb-4"></div>
        <p>Verifying your email...</p>
      </div>
    </div>
  );
}
