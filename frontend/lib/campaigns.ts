import {apiFetch} from "@/lib/api";
import type {Campaign, CampaignCreate, CatalogOption, Offer} from "@/types/campaign";

export async function getCampaigns(): Promise<Campaign[]> {
  return apiFetch<Campaign[]>("/local/campaigns");
}

export async function syncCampaigns(): Promise<void> {
  await apiFetch("/sync", {
    method: "POST",
  });
}

export async function syncCampaign(campaignId: number): Promise<Campaign> {
  return apiFetch<Campaign>(`/local/campaigns/${campaignId}/sync`, {
    method: "POST",
  });
}

export async function restoreCampaign(campaignId: number): Promise<Campaign> {
  return apiFetch<Campaign>(`/local/campaigns/${campaignId}/restore`, {
    method: "POST",
  });
}

export async function restoreStreamOffer(
  streamId: number,
  offerId: number,
): Promise<Campaign> {
  return apiFetch<Campaign>(
    `/local/streams/${streamId}/offers/${offerId}/restore`,
    {
      method: "POST",
    },
  );
}

export async function deleteStreamOffer(
  streamId: number,
  offerId: number,
): Promise<Campaign> {
  return apiFetch<Campaign>(
    `/local/streams/${streamId}/offers/${offerId}/delete`,
    {
      method: "POST",
    },
  );
}

export async function addStreamOffers(
  streamId: number,
  offerIds: number[],
): Promise<Campaign> {
  return apiFetch<Campaign>(`/local/streams/${streamId}/offers`, {
    method: "POST",
    body: JSON.stringify({ offer_ids: offerIds }),
  });
}

export async function pushStream(streamId: number): Promise<Campaign> {
  return apiFetch<Campaign>(`/local/streams/${streamId}/push`, {
    method: "POST",
  });
}

export async function cancelStream(streamId: number): Promise<Campaign> {
  return apiFetch<Campaign>(`/local/streams/${streamId}/cancel`, {
    method: "POST",
  });
}

export async function createCampaign(
  data: CampaignCreate,
): Promise<{ campaign: Campaign }> {
  return apiFetch<{ campaign: Campaign }>("/campaigns", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function searchOffers(search: string): Promise<Offer[]> {
  return apiFetch<Offer[]>(`/offers?search=${encodeURIComponent(search)}`)
}

export async function getDomains(): Promise<CatalogOption[]> {
  return apiFetch<CatalogOption[]>("/domains");
}

export async function getCampaignGroups(): Promise<CatalogOption[]> {
  return apiFetch<CatalogOption[]>("/groups?type=campaigns");
}

export async function getTrafficSources(): Promise<CatalogOption[]> {
  return apiFetch<CatalogOption[]>("/traffic-sources");
}

export async function setOfferPin(
  streamId: number,
  offerId: number,
  isPinned: boolean,
): Promise<Campaign> {
  return apiFetch<Campaign>(
    `/local/streams/${streamId}/offers/${offerId}/pin`,
    {
      method: "PATCH",
      body: JSON.stringify({ is_pinned: isPinned }),
    },
  );
}