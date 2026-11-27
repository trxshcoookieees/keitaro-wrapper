"use client";

import {useEffect, useState} from "react";
import {OfferSearch} from "@/components/campaigns/OfferSearch";
import {
  createCampaign,
  getCampaignGroups,
  getDomains,
  getTrafficSources,
} from "@/lib/campaigns";
import type {Campaign, CatalogOption, Offer} from "@/types/campaign";

interface CreateCampaignModalProps {
  onClose: () => void;
  onCreated: (campaign: Campaign) => void;
}

export function CreateCampaignModal({
                                      onClose,
                                      onCreated,
                                    }: CreateCampaignModalProps) {
  const [name, setName] = useState("");
  const [geoInput, setGeoInput] = useState("");
  const [domains, setDomains] = useState<CatalogOption[]>([]);
  const [groups, setGroups] = useState<CatalogOption[]>([]);
  const [trafficSources, setTrafficSources] = useState<CatalogOption[]>([]);
  const [domainId, setDomainId] = useState<number | null>(null);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [trafficSourceId, setTrafficSourceId] = useState<number | null>(null);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [selectedOffers, setSelectedOffers] = useState<Offer[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadOptions() {
      try {
        setLoadingOptions(true);

        const [domainList, groupList, sourceList] = await Promise.all([
          getDomains(),
          getCampaignGroups(),
          getTrafficSources(),
        ]);

        if (!active) {
          return;
        }

        setDomains(domainList);
        setGroups(groupList);
        setTrafficSources(sourceList);

        setDomainId(domainList[0]?.id ?? null);
        setGroupId(groupList[0]?.id ?? null);
        setTrafficSourceId(sourceList[0]?.id ?? null);
      } catch (error) {
        if (!active) {
          return;
        }

        setError(
          error instanceof Error
            ? error.message
            : "Failed to load domains, groups and traffic sources",
        );
      } finally {
        if (active) {
          setLoadingOptions(false);
        }
      }
    }

    loadOptions();

    return () => {
      active = false;
    };
  }, []);

  function toggleOffer(offer: Offer) {
    setSelectedOffers((current) => {
      const alreadySelected = current.some((item) => item.id === offer.id);

      if (alreadySelected) {
        return current.filter((item) => item.id !== offer.id);
      }

      return [...current, offer];
    });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const geoCodes = geoInput
      .split(",")
      .map((code) => code.trim().toUpperCase())
      .filter(Boolean);

    if (!name.trim()) {
      setError("Campaign name is required");
      return;
    }

    if (geoCodes.length === 0) {
      setError("Add at least one GEO code");
      return;
    }

    if (selectedOffers.length === 0) {
      setError("Select at least one offer");
      return;
    }

    if (
      domainId === null ||
      groupId === null ||
      trafficSourceId === null
    ) {
      setError("Select domain, group and traffic source");
      return;
    }

    try {
      setSubmitting(true);

      const result = await createCampaign({
        name: name.trim(),
        geo_codes: geoCodes,
        offer_ids: selectedOffers.map((offer) => offer.id),
        domain_id: domainId,
        group_id: groupId,
        traffic_source_id: trafficSourceId,
      });

      onCreated(result.campaign);
      onClose();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to create campaign",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold">Create campaign</h2>

          <button
            type="button"
            onClick={onClose}
            className="text-xl text-gray-400 hover:text-gray-700"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 p-6">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Campaign name
            </label>

            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="test_surname_campaign"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              GEO codes
            </label>

            <input
              value={geoInput}
              onChange={(event) => setGeoInput(event.target.value)}
              placeholder="MX, AU, RO"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500"
            />

            <p className="mt-1 text-xs text-gray-400">
              Separate country codes with commas
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Domain
              </label>

              <select
                value={domainId ?? ""}
                onChange={(event) =>
                  setDomainId(
                    event.target.value ? Number(event.target.value) : null,
                  )
                }
                disabled={loadingOptions}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500 disabled:bg-gray-50"
              >
                {loadingOptions && <option value="">Loading...</option>}

                {!loadingOptions && domains.length === 0 && (
                  <option value="">No domains</option>
                )}

                {domains.map((domain) => (
                  <option key={domain.id} value={domain.id}>
                    {domain.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Group
              </label>

              <select
                value={groupId ?? ""}
                onChange={(event) =>
                  setGroupId(
                    event.target.value ? Number(event.target.value) : null,
                  )
                }
                disabled={loadingOptions}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500 disabled:bg-gray-50"
              >
                {loadingOptions && <option value="">Loading...</option>}

                {!loadingOptions && groups.length === 0 && (
                  <option value="">No groups</option>
                )}

                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Traffic source
              </label>

              <select
                value={trafficSourceId ?? ""}
                onChange={(event) =>
                  setTrafficSourceId(
                    event.target.value ? Number(event.target.value) : null,
                  )
                }
                disabled={loadingOptions}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500 disabled:bg-gray-50"
              >
                {loadingOptions && <option value="">Loading...</option>}

                {!loadingOptions && trafficSources.length === 0 && (
                  <option value="">No sources</option>
                )}

                {trafficSources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Search offers
            </label>

            <OfferSearch
              selectedOfferIds={selectedOffers.map((offer) => offer.id)}
              onSelect={toggleOffer}
              disabled={submitting}
            />
          </div>

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
                    onClick={() => toggleOffer(offer)}
                    className="rounded-md bg-gray-100 px-2.5 py-1.5 text-xs text-gray-700 hover:bg-gray-200"
                  >
                    {offer.name} ×
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <div className="flex justify-end gap-3 border-t border-gray-100 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Creating..." : "Create campaign"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}