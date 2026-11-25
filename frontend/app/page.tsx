"use client";

import { useEffect, useState } from "react";
import { CampaignSidebar } from "@/components/campaigns/CampaignSidebar";
import { CampaignContent } from "@/components/campaigns/CampaignContent";
import { CreateCampaignModal } from "@/components/campaigns/CreateCampaignModal";
import { getCampaigns } from "@/lib/campaigns";
import type { Campaign } from "@/types/campaign";

export default function Home() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(
    null,
  );
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadCampaigns() {
      try {
        const data = await getCampaigns();

        setCampaigns(data);

        if (data.length > 0) {
          setSelectedCampaignId(data[0].id);
        }
      } catch (error) {
        setError(
          error instanceof Error ? error.message : "Failed to load campaigns",
        );
      } finally {
        setLoading(false);
      }
    }

    loadCampaigns();
  }, []);

  const selectedCampaign =
    campaigns.find((campaign) => campaign.id === selectedCampaignId) ?? null;

  function handleCampaignCreated(campaign: Campaign) {
    setCampaigns((current) => [campaign, ...current]);
    setSelectedCampaignId(campaign.id);
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-gray-500">
        Loading campaigns...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <CampaignSidebar
        campaigns={campaigns}
        selectedCampaignId={selectedCampaignId}
        onSelect={setSelectedCampaignId}
        onAdd={() => setIsModalOpen(true)}
      />

      <CampaignContent campaign={selectedCampaign} />

      {isModalOpen && (
        <CreateCampaignModal
          onClose={() => setIsModalOpen(false)}
          onCreated={handleCampaignCreated}
        />
      )}
    </div>
  );
}