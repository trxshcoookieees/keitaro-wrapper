"use client";

import { useState } from "react";
import { OfferSearch } from "@/components/campaigns/OfferSearch";
import { addStreamOffers } from "@/lib/campaigns";
import type { Campaign, Offer } from "@/types/campaign";

interface AddStreamOffersProps {
  streamId: number;
  existingOfferIds: number[];
  onCampaignUpdated: (campaign: Campaign) => void;
  disabled?: boolean;
}

export function AddStreamOffers({
  streamId,
  existingOfferIds,
  onCampaignUpdated,
  disabled = false,
}: AddStreamOffersProps) {
  const [open, setOpen] = useState(false);
  const [selectedOffers, setSelectedOffers] = useState<Offer[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function selectOffer(offer: Offer) {
    setSelectedOffers((current) => {
      if (current.some((item) => item.id === offer.id)) {
        return current;
      }

      return [...current, offer];
    });
  }

  function removeOffer(offerId: number) {
    setSelectedOffers((current) =>
      current.filter((item) => item.id !== offerId),
    );
  }

  function reset() {
    setSelectedOffers([]);
    setError("");
    setOpen(false);
  }

  async function handleSubmit() {
    if (selectedOffers.length === 0) {
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      const updated = await addStreamOffers(
        streamId,
        selectedOffers.map((offer) => offer.id),
      );

      onCampaignUpdated(updated);
      reset();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to add offers to stream",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const hiddenOfferIds = [
    ...existingOfferIds,
    ...selectedOffers.map((offer) => offer.id),
  ];

  return (
    <div className="border-t border-gray-200 px-5 py-4">
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          disabled={disabled}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Add offers
        </button>
      ) : (
        <div className="space-y-3">
          <OfferSearch
            selectedOfferIds={hiddenOfferIds}
            onSelect={selectOffer}
            disabled={submitting}
          />

          {selectedOffers.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">
                Selected offers ({selectedOffers.length})
              </p>

              <div className="flex flex-wrap gap-2">
                {selectedOffers.map((offer) => (
                  <button
                    key={offer.id}
                    type="button"
                    onClick={() => removeOffer(offer.id)}
                    disabled={submitting}
                    className="rounded-md bg-gray-100 px-2.5 py-1.5 text-xs text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {offer.name} ×
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={
                submitting || selectedOffers.length === 0 || disabled
              }
              className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Adding..." : "Add offers"}
            </button>

            <button
              type="button"
              onClick={reset}
              disabled={submitting}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
