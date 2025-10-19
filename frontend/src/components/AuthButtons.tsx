import { useState } from 'react';
import RegisterForm from './RegisterForm';

export default function AuthButtons() {
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [user, setUser] = useState<{ id: string; username: string; email: string } | null>(null);

  const handleRegisterSuccess = (userData: { id: string; username: string; email: string }) => {
    setUser(userData);
    setShowRegisterForm(false);
    alert(`Welcome, ${userData.username}! Registration successful.`);
  };

  if (user) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-gray-700">Welcome, {user.username}!</span>
        <button
          onClick={() => setUser(null)}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-full hover:bg-gray-50"
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="flex gap-3">
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 shadow">
          Log in
        </button>
        <button
          onClick={() => setShowRegisterForm(true)}
          className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-full hover:bg-indigo-50"
        >
          Register
        </button>
      </div>

      {showRegisterForm && (
        <RegisterForm
          onClose={() => setShowRegisterForm(false)}
          onSuccess={handleRegisterSuccess}
        />
      )}
    </>
  );
}

