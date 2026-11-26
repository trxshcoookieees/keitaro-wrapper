"use client";

import { useEffect, useState } from "react";
import { CampaignSidebar } from "@/components/campaigns/CampaignSidebar";
import { CampaignContent } from "@/components/campaigns/CampaignContent";
import { CreateCampaignModal } from "@/components/campaigns/CreateCampaignModal";
import { getCampaigns, syncCampaign, syncCampaigns } from "@/lib/campaigns";
import type { Campaign } from "@/types/campaign";

export default function Home() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(
    null,
  );
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updateError, setUpdateError] = useState("");

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

  function replaceCampaign(updated: Campaign) {
    setCampaigns((current) =>
      current.map((campaign) =>
        campaign.id === updated.id ? updated : campaign,
      ),
    );
  }

  function handleCampaignCreated(campaign: Campaign) {
    setCampaigns((current) => [campaign, ...current]);
    setSelectedCampaignId(campaign.id);
  }

  async function handleUpdateActiveCampaign() {
    if (selectedCampaignId === null) {
      return;
    }

    try {
      setUpdating(true);
      setUpdateError("");

      const updated = await syncCampaign(selectedCampaignId);

      replaceCampaign(updated);
    } catch (error) {
      setUpdateError(
        error instanceof Error ? error.message : "Failed to update campaign",
      );
    } finally {
      setUpdating(false);
    }
  }

  async function handleFetch() {
    try {
      setFetching(true);
      setError("");

      await syncCampaigns();

      const data = await getCampaigns();
      setCampaigns(data);

      if (!data.some((campaign) => campaign.id === selectedCampaignId)) {
        setSelectedCampaignId(data[0]?.id ?? null);
      }
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to fetch campaigns",
      );
    } finally {
      setFetching(false);
    }
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
        onSelect={(campaignId) => {
          setSelectedCampaignId(campaignId);
          setUpdateError("");
        }}
        onAdd={() => setIsModalOpen(true)}
        onFetch={handleFetch}
        fetching={fetching}
      />

      <CampaignContent
        campaign={selectedCampaign}
        onUpdate={handleUpdateActiveCampaign}
        updating={updating}
        updateError={updateError}
        onCampaignUpdated={replaceCampaign}
      />

      {isModalOpen && (
        <CreateCampaignModal
          onClose={() => setIsModalOpen(false)}
          onCreated={handleCampaignCreated}
        />
      )}
    </div>
  );
}