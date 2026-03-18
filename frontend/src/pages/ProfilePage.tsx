import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Mail, LogOut, Edit2, Check, X } from "lucide-react";

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSave = async () => {
    setErrorMessage("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      await updateProfile({ full_name: fullName });
      setSuccessMessage("Profile updated successfully");
      setIsEditing(false);

      // Hide success message after 3 seconds
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (!user) {
    return null;
  }

  const initials = (user.full_name || user.email)
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 rounded-lg shadow-2xl p-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-white">Profile</h1>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-600/10 hover:bg-red-600/20 border border-red-500/30 text-red-400 rounded-lg transition"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>

          {successMessage && (
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg text-green-400">
              {successMessage}
            </div>
          )}

          {errorMessage && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
              {errorMessage}
            </div>
          )}

          {/* Avatar */}
          <div className="flex justify-center mb-8">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
              <span className="text-3xl font-bold text-white">{initials}</span>
            </div>
          </div>

          {/* Profile Info */}
          <div className="space-y-6">
            {/* Email */}
            <div className="bg-slate-700/30 rounded-lg p-4 border border-purple-500/10">
              <div className="flex items-center gap-2 mb-2">
                <Mail size={18} className="text-purple-400" />
                <label className="text-sm font-medium text-gray-300">Email</label>
              </div>
              <p className="text-white text-lg font-semibold">{user.email}</p>
            </div>

            {/* Full Name */}
            <div className="bg-slate-700/30 rounded-lg p-4 border border-purple-500/10">
              <label className="text-sm font-medium text-gray-300 block mb-2">Full Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                  placeholder="Enter your full name"
                />
              ) : (
                <p className="text-white text-lg font-semibold">{fullName || "Not set"}</p>
              )}
            </div>

            {/* Created At */}
            <div className="bg-slate-700/30 rounded-lg p-4 border border-purple-500/10">
              <label className="text-sm font-medium text-gray-300 block mb-2">Member Since</label>
              <p className="text-white text-lg">
                {new Date(user.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 mt-8">
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
              >
                <Edit2 size={18} />
                Edit Profile
              </button>
            ) : (
              <>
                <button
                  onClick={handleSave}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition disabled:opacity-50"
                >
                  <Check size={18} />
                  {isLoading ? "Saving..." : "Save"}
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setFullName(user.full_name || "");
                  }}
                  className="flex items-center gap-2 px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition"
                >
                  <X size={18} />
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
