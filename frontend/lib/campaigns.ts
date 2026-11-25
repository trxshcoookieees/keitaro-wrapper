import {apiFetch} from "@/lib/api";
import type {Campaign, CampaignCreate, Offer} from "@/types/campaign";

export async function getCampaigns(): Promise<Campaign[]> {
  return apiFetch<Campaign[]>("/local/campaigns");
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