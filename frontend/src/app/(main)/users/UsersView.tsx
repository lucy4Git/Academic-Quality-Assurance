"use client";

import { useState } from "react";
import {
  usePendingUsers,
  useAllUsers,
  useApproveUser,
  useRejectUser,
  type PendingUser,
} from "@/hooks/useAdminUsers";

const ROLE_OPTIONS = [
  { value: "lecturer", label: "Lecturer" },
  { value: "programme_coordinator", label: "Programme Coordinator" },
  { value: "head_of_department", label: "Head of Department" },
  { value: "faculty_dean", label: "Faculty Dean" },
  { value: "quality_assurance_officer", label: "QA Officer" },
  { value: "system_admin", label: "System Admin" },
];

type Tab = "pending" | "approved" | "rejected" | "all";

function StatusBadge({ status, isVerified }: { status: string; isVerified: boolean }) {
  const statusColour =
    status === "approved"
      ? "bg-green-100 text-green-700"
      : status === "rejected"
      ? "bg-red-100 text-red-700"
      : "bg-yellow-100 text-yellow-700";

  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColour}`}>
        {status}
      </span>
      <span
        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
          isVerified ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-500"
        }`}
      >
        {isVerified ? "email verified" : "unverified"}
      </span>
    </div>
  );
}

function ApproveModal({
  user,
  onClose,
  onConfirm,
  isPending,
}: {
  user: PendingUser;
  onClose: () => void;
  onConfirm: (role: string, institutionId: string | null) => void;
  isPending: boolean;
}) {
  const [role, setRole] = useState(user.role_requested ?? "lecturer");
  const [institutionId, setInstitutionId] = useState<string>("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">Approve Registration</h2>
        <p className="mt-1 text-sm text-gray-500">
          Approving <strong>{user.full_name}</strong> ({user.email})
        </p>

        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Assign Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Institution ID{" "}
              <span className="font-normal text-gray-400">(optional UUID)</span>
            </label>
            <input
              type="text"
              value={institutionId}
              onChange={(e) => setInstitutionId(e.target.value)}
              placeholder="Leave blank to assign later"
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {user.reason_for_access && (
            <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
              <p className="text-xs font-medium text-gray-500 mb-1">Reason for access</p>
              {user.reason_for_access}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(role, institutionId.trim() || null)}
            disabled={isPending}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {isPending ? "Approving…" : "Approve"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RejectModal({
  user,
  onClose,
  onConfirm,
  isPending,
}: {
  user: PendingUser;
  onClose: () => void;
  onConfirm: (reason: string | null) => void;
  isPending: boolean;
}) {
  const [reason, setReason] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">Reject Registration</h2>
        <p className="mt-1 text-sm text-gray-500">
          Rejecting <strong>{user.full_name}</strong> ({user.email})
        </p>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason for rejection{" "}
            <span className="font-normal text-gray-400">(optional — sent to user)</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            placeholder="e.g. Unable to verify institutional affiliation"
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
          />
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(reason.trim() || null)}
            disabled={isPending}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {isPending ? "Rejecting…" : "Reject"}
          </button>
        </div>
      </div>
    </div>
  );
}

function UserCard({
  user,
  onApprove,
  onReject,
}: {
  user: PendingUser;
  onApprove: (user: PendingUser) => void;
  onReject: (user: PendingUser) => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-gray-900 text-sm">{user.full_name}</p>
            <StatusBadge status={user.approval_status} isVerified={user.is_verified} />
          </div>
          <p className="mt-0.5 text-sm text-gray-500">{user.email}</p>

          <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
            {user.role_requested && (
              <span>
                <span className="font-medium text-gray-700">Requested role:</span>{" "}
                {user.role_requested.replace(/_/g, " ")}
              </span>
            )}
            {user.institution_name_requested && (
              <span>
                <span className="font-medium text-gray-700">Institution:</span>{" "}
                {user.institution_name_requested}
              </span>
            )}
            <span>
              <span className="font-medium text-gray-700">Registered:</span>{" "}
              {new Date(user.created_at).toLocaleDateString()}
            </span>
          </div>

          {user.reason_for_access && (
            <p className="mt-2 text-xs text-gray-600 italic line-clamp-2">
              &ldquo;{user.reason_for_access}&rdquo;
            </p>
          )}
        </div>

        {user.approval_status === "pending" && (
          <div className="flex shrink-0 flex-col gap-2">
            <button
              onClick={() => onApprove(user)}
              className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => onReject(user)}
              className="rounded-lg border border-red-300 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              Reject
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function UsersView() {
  const [tab, setTab] = useState<Tab>("pending");
  const [approveTarget, setApproveTarget] = useState<PendingUser | null>(null);
  const [rejectTarget, setRejectTarget] = useState<PendingUser | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const { data: pendingUsers, isLoading: pendingLoading } = usePendingUsers();
  const { data: approvedUsers, isLoading: approvedLoading } = useAllUsers(
    tab === "approved" ? "approved" : undefined
  );
  const { data: rejectedUsers, isLoading: rejectedLoading } = useAllUsers(
    tab === "rejected" ? "rejected" : undefined
  );
  const { data: allUsers, isLoading: allLoading } = useAllUsers(
    tab === "all" ? undefined : undefined
  );

  const approve = useApproveUser();
  const reject = useRejectUser();

  const showToast = (type: "success" | "error", msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  const handleApproveConfirm = async (role: string, institutionId: string | null) => {
    if (!approveTarget) return;
    try {
      await approve.mutateAsync({
        user_id: approveTarget.id,
        role,
        institution_id: institutionId,
      });
      setApproveTarget(null);
      showToast("success", `${approveTarget.full_name} approved successfully.`);
    } catch {
      showToast("error", "Failed to approve user. Please try again.");
    }
  };

  const handleRejectConfirm = async (reason: string | null) => {
    if (!rejectTarget) return;
    try {
      await reject.mutateAsync({ user_id: rejectTarget.id, reason });
      setRejectTarget(null);
      showToast("success", `${rejectTarget.full_name} has been rejected.`);
    } catch {
      showToast("error", "Failed to reject user. Please try again.");
    }
  };

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: "pending", label: "Pending", count: pendingUsers?.length },
    { key: "approved", label: "Approved" },
    { key: "rejected", label: "Rejected" },
    { key: "all", label: "All Users" },
  ];

  const currentUsers =
    tab === "pending"
      ? pendingUsers
      : tab === "approved"
      ? approvedUsers
      : tab === "rejected"
      ? rejectedUsers
      : allUsers;

  const isLoading =
    tab === "pending"
      ? pendingLoading
      : tab === "approved"
      ? approvedLoading
      : tab === "rejected"
      ? rejectedLoading
      : allLoading;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed right-6 top-6 z-50 rounded-xl px-5 py-3 text-sm font-medium text-white shadow-lg transition-all ${
            toast.type === "success" ? "bg-green-600" : "bg-red-600"
          }`}
        >
          {toast.msg}
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Review registrations, approve or reject access, and assign roles.
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 rounded-xl bg-gray-100 p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span className="rounded-full bg-yellow-500 px-1.5 py-0.5 text-xs font-semibold text-white leading-none">
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      ) : !currentUsers || currentUsers.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 py-16 text-center">
          <p className="text-lg font-semibold text-gray-700">
            {tab === "pending" ? "No pending registrations" : "No users found"}
          </p>
          <p className="mt-1 text-sm text-gray-400">
            {tab === "pending"
              ? "All registrations have been reviewed."
              : "Switch tabs to see other users."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {currentUsers.map((u) => (
            <UserCard
              key={u.id}
              user={u}
              onApprove={setApproveTarget}
              onReject={setRejectTarget}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      {approveTarget && (
        <ApproveModal
          user={approveTarget}
          onClose={() => setApproveTarget(null)}
          onConfirm={handleApproveConfirm}
          isPending={approve.isPending}
        />
      )}
      {rejectTarget && (
        <RejectModal
          user={rejectTarget}
          onClose={() => setRejectTarget(null)}
          onConfirm={handleRejectConfirm}
          isPending={reject.isPending}
        />
      )}
    </div>
  );
}
