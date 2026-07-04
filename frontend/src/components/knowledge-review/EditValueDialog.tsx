"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { KnowledgeReviewItem } from "@/types/knowledge-review";

interface EditValueDialogProps {
  item: KnowledgeReviewItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (itemId: string, editedValue: string, reason: string) => void;
  isPending: boolean;
}

/**
 * Modal dialog that allows a QA officer to provide a corrected value for
 * a review item and an optional reason for the edit.
 */
export function EditValueDialog({
  item,
  open,
  onOpenChange,
  onSubmit,
  isPending,
}: EditValueDialogProps) {
  const [editedValue, setEditedValue] = useState(
    item?.edited_value ?? item?.extracted_value ?? ""
  );
  const [reason, setReason] = useState("");

  // Sync form state when item changes
  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen && item) {
      setEditedValue(item.edited_value ?? item.extracted_value);
      setReason("");
    }
    onOpenChange(nextOpen);
  };

  const handleSubmit = () => {
    if (!item || !editedValue.trim()) return;
    onSubmit(item.id, editedValue.trim(), reason.trim());
  };

  if (!item) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Extracted Value</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Context */}
          <div className="rounded-lg bg-muted/50 border p-3 space-y-1 text-sm">
            <p className="text-muted-foreground">
              <span className="font-medium text-foreground">{item.entity_key}</span>
              {" · "}
              <span className="text-muted-foreground">{item.field_name}</span>
            </p>
            <p className="text-muted-foreground text-xs">
              Original extracted value:{" "}
              <span className="font-mono text-foreground">{item.extracted_value}</span>
            </p>
          </div>

          {/* Edited value */}
          <div className="space-y-1.5">
            <Label htmlFor="edited-value">Corrected Value</Label>
            <Textarea
              id="edited-value"
              value={editedValue}
              onChange={(e) => setEditedValue(e.target.value)}
              placeholder="Enter the corrected value…"
              rows={3}
              className="font-mono text-sm resize-none"
            />
          </div>

          {/* Reason */}
          <div className="space-y-1.5">
            <Label htmlFor="edit-reason">
              Reason{" "}
              <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Textarea
              id="edit-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why was this value corrected?"
              rows={2}
              className="resize-none"
            />
          </div>
        </div>

        <DialogFooter showCloseButton>
          <Button
            onClick={handleSubmit}
            disabled={isPending || !editedValue.trim()}
          >
            {isPending ? "Saving…" : "Save Edit"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
