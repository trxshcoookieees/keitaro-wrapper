"use client";

import { useEffect, useState } from "react";
import { searchOffers } from "@/lib/campaigns";
import type { Offer } from "@/types/campaign";

interface OfferSearchProps {
  selectedOfferIds?: number[];
  onSelect: (offer: Offer) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function OfferSearch({
  selectedOfferIds = [],
  onSelect,
  placeholder = "Search by offer name or ID",
  disabled = false,
}: OfferSearchProps) {
  const [search, setSearch] = useState("");
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!search.trim()) {
      setOffers([]);
      setError("");
      return;
    }

    let active = true;

    const timeout = setTimeout(async () => {
      try {
        setLoading(true);
        setError("");

        const result = await searchOffers(search.trim());

        if (active) {
          setOffers(result);
        }
      } catch {
        if (active) {
          setError("Failed to load offers");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [search]);

  const visibleOffers = offers.filter(
    (offer) => !selectedOfferIds.includes(offer.id),
  );

  return (
    <div>
      <input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500 disabled:bg-gray-50"
      />

      {(search.trim() || loading) && (
        <div className="mt-2 max-h-40 overflow-y-auto rounded-lg border border-gray-200">
          {loading && (
            <p className="p-3 text-sm text-gray-400">Searching...</p>
          )}

          {!loading &&
            visibleOffers.map((offer) => (
              <button
                key={offer.id}
                type="button"
                onClick={() => onSelect(offer)}
                disabled={disabled}
                className="flex w-full items-center justify-between border-b border-gray-100 px-3 py-2 text-left text-sm last:border-0 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span>{offer.name}</span>
                <span className="text-gray-400">#{offer.id}</span>
              </button>
            ))}

          {!loading && search.trim() && visibleOffers.length === 0 && (
            <p className="p-3 text-sm text-gray-400">No offers found</p>
          )}
        </div>
      )}

      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
