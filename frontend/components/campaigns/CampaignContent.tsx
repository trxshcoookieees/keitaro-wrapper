"use client";

import { useState } from "react";
import { deleteStreamOffer, restoreStreamOffer } from "@/lib/campaigns";
import type { Campaign } from "@/types/campaign";

interface CampaignContentProps {
  campaign: Campaign | null;
  onUpdate: () => void;
  updating: boolean;
  updateError: string;
  onCampaignUpdated: (campaign: Campaign) => void;
}

export function CampaignContent({
  campaign,
  onUpdate,
  updating,
  updateError,
  onCampaignUpdated,
}: CampaignContentProps) {
  const [offerActionKey, setOfferActionKey] = useState<string | null>(null);
  const [offerActionError, setOfferActionError] = useState("");

  async function handleOfferAction(
    streamId: number,
    offerId: number,
    action: "delete" | "restore",
  ) {
    const key = `${action}:${streamId}:${offerId}`;

    try {
      setOfferActionKey(key);
      setOfferActionError("");

      const updated =
        action === "delete"
          ? await deleteStreamOffer(streamId, offerId)
          : await restoreStreamOffer(streamId, offerId);

      onCampaignUpdated(updated);
    } catch (error) {
      setOfferActionError(
        error instanceof Error
          ? error.message
          : `Failed to ${action} offer`,
      );
    } finally {
      setOfferActionKey(null);
    }
  }

  if (!campaign) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-gray-400">
          Select a campaign to view its streams
        </p>
      </main>
    );
  }

  return (
    <main className="min-w-0 flex-1 overflow-y-auto p-8">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-950">
            {campaign.name}
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Campaign ID: {campaign.keitaro_id ?? "Not synchronized"}
          </p>
        </div>

        <button
          onClick={onUpdate}
          disabled={updating || campaign.keitaro_id === null}
          title={
            campaign.keitaro_id === null
              ? "Campaign is not synchronized with Keitaro"
              : "Refresh this campaign from Keitaro"
          }
          className="shrink-0 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {updating ? "Updating..." : "Update"}
        </button>
      </div>

      {updateError && (
        <p className="mb-4 text-sm text-red-600">{updateError}</p>
      )}

      {offerActionError && (
        <p className="mb-4 text-sm text-red-600">{offerActionError}</p>
      )}

      <div className="space-y-6">
        {campaign.streams?.map((stream) => (
          <section
            key={stream.id}
            className="overflow-hidden rounded-xl border border-gray-200 bg-white"
          >
            <div className="border-b border-gray-200 px-5 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-gray-900">
                    {stream.name}
                  </h2>

                  <p className="mt-1 text-xs text-gray-500">
                    {stream.type} · {stream.schema} · ID:{" "}
                    {stream.keitaro_id ?? "Not synchronized"}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {stream.is_dirty && (
                    <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
                      Unsaved changes
                    </span>
                  )}

                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                      stream.is_active
                        ? "bg-green-50 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {stream.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
              </div>

              {stream.action_payload && (
                <p className="mt-3 break-all text-sm text-gray-500">
                  Destination: {stream.action_payload}
                </p>
              )}
            </div>

            {stream.offers?.length > 0 ? (
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="px-5 py-3 font-medium">Offer ID</th>
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Share</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Actions</th>
                </tr>
                </thead>

                <tbody className="divide-y divide-gray-100">
                {stream.offers.map((offer) => (
                  <tr key={offer.id}>
                    <td className="px-5 py-3 text-gray-500">
                      {offer.offer_id}
                    </td>
                    <td className="px-5 py-3 font-medium text-gray-900">
                      {offer.offer_name}
                    </td>
                    <td className="px-5 py-3 text-gray-700">
                      {offer.share}%
                    </td>
                    <td className="px-5 py-3">
                        <span
                          className={
                            offer.is_active
                              ? "text-green-700"
                              : "text-gray-400"
                          }
                        >
                          {offer.is_active ? "Active" : "Inactive"}
                        </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      {offer.is_active ? (
                        <button
                          onClick={() =>
                            handleOfferAction(
                              stream.id,
                              offer.offer_id,
                              "delete",
                            )
                          }
                          disabled={offerActionKey !== null}
                          className="rounded-md border border-red-200 px-2.5 py-1 text-xs font-medium text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {offerActionKey ===
                          `delete:${stream.id}:${offer.offer_id}`
                            ? "Deleting..."
                            : "Delete"}
                        </button>
                      ) : offer.share === 0 ? (
                        <button
                          onClick={() =>
                            handleOfferAction(
                              stream.id,
                              offer.offer_id,
                              "restore",
                            )
                          }
                          disabled={offerActionKey !== null}
                          className="rounded-md border border-gray-300 px-2.5 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {offerActionKey ===
                          `restore:${stream.id}:${offer.offer_id}`
                            ? "Restoring..."
                            : "Restore"}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
                </tbody>
              </table>
            ) : (
              <div className="px-5 py-6 text-sm text-gray-400">
                No offers in this stream
              </div>
            )}
          </section>
        ))}

        {campaign.streams?.length === 0 && (
          <p className="text-sm text-gray-400">This campaign has no streams.</p>
        )}
      </div>
    </main>
  );
}