import React, { createContext, useEffect, useState, ReactNode } from "react";

interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  email_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
  logout: () => void;
  updateProfile: (profile: Partial<User>) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

// Helper function to make requests with timeout
const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeoutMs = 10000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token and user on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    const cachedUser = localStorage.getItem("auth_user");

    if (storedToken) {
      setToken(storedToken);
      
      // Use cached user if available to speed up initial load
      if (cachedUser) {
        try {
          setUser(JSON.parse(cachedUser));
          setIsLoading(false);
          // Verify token validity in background (don't block UI)
          verifyTokenAsync(storedToken);
        } catch {
          // Invalid cache, fetch fresh
          fetchUser(storedToken);
        }
      } else {
        // No cache, fetch user
        fetchUser(storedToken);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  // Verify token asynchronously in background
  const verifyTokenAsync = async (authToken: string) => {
    try {
      const response = await fetchWithTimeout("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      }, 5000);

      if (!response.ok) {
        throw new Error("Token invalid");
      }

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem("auth_user", JSON.stringify(userData));
    } catch (error) {
      console.error("Token verification failed:", error);
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      setToken(null);
      setUser(null);
    }
  };

  const fetchUser = async (authToken: string) => {
    try {
      const response = await fetchWithTimeout("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      }, 5000);

      if (!response.ok) {
        throw new Error("Failed to fetch user");
      }

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem("auth_user", JSON.stringify(userData));
    } catch (error) {
      console.error("Error fetching user:", error);
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await fetchWithTimeout("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      }, 15000); // Longer timeout for password verification

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
      }

      const data = await response.json();
      
      // Store token and user immediately (no second fetch needed)
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem("auth_token", data.access_token);
      localStorage.setItem("auth_user", JSON.stringify(data.user));
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, full_name?: string) => {
    try {
      const response = await fetchWithTimeout("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, full_name }),
      }, 15000);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Registration failed");
      }

      const data = await response.json();
      
      // Store token and user immediately
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem("auth_token", data.access_token);
      localStorage.setItem("auth_user", JSON.stringify(data.user));
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
  };

  const updateProfile = async (profileData: Partial<User>) => {
    if (!token) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await fetchWithTimeout("/api/auth/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(profileData),
      }, 10000);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update profile");
      }

      const updatedUser = await response.json();
      setUser(updatedUser);
      localStorage.setItem("auth_user", JSON.stringify(updatedUser));
    } catch (error) {
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    register,
    logout,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
