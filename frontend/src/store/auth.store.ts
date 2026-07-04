import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User, UserRole } from "@/types";
import { AUDIT_TRIGGER_ROLES, UPLOAD_ROLES, RESOLVE_ROLES } from "@/lib/constants";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setUser: (user: User) => void;
  clearUser: () => void;
  setLoading: (loading: boolean) => void;

  // Derived role helpers
  hasRole: (...roles: UserRole[]) => boolean;
  canTriggerAudit: () => boolean;
  canUpload: () => boolean;
  canResolveFindings: () => boolean;
  isAdmin: () => boolean;
  isQAOfficer: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) =>
        set({ user, isAuthenticated: true, isLoading: false }),

      clearUser: () =>
        set({ user: null, isAuthenticated: false, isLoading: false }),

      setLoading: (loading) => set({ isLoading: loading }),

      hasRole: (...roles) => {
        const { user } = get();
        if (!user) return false;
        return roles.includes(user.role);
      },

      canTriggerAudit: () => {
        const { user } = get();
        if (!user) return false;
        return AUDIT_TRIGGER_ROLES.includes(user.role);
      },

      canUpload: () => {
        const { user } = get();
        if (!user) return false;
        return UPLOAD_ROLES.includes(user.role);
      },

      canResolveFindings: () => {
        const { user } = get();
        if (!user) return false;
        return RESOLVE_ROLES.includes(user.role);
      },

      isAdmin: () => get().user?.role === "system_admin",

      isQAOfficer: () =>
        get().user?.role === "quality_assurance_officer" ||
        get().user?.role === "system_admin",
    }),
    {
      name: "aqaa-auth",
      // Only persist non-sensitive user metadata; never persist tokens
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
