import {apiFetch} from "@/lib/api";
import type {Campaign, CampaignCreate, Offer} from "@/types/campaign";

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
