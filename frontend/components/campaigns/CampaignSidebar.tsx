import type {Campaign} from "@/types/campaign";

interface CampaignSidebarProps {
  campaigns: Campaign[];
  selectedCampaignId: number | null;
  onSelect: (campaignId: number) => void;
  onAdd: () => void;
}

export function CampaignSidebar({
                                  campaigns,
                                  selectedCampaignId,
                                  onSelect,
                                  onAdd,
                                }: CampaignSidebarProps) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-gray-200 bg-white">
      <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
        <h2 className="text-lg font-semibold">Campaigns</h2>

        <button
          onClick={onAdd}
          className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-gray-700"
        >
          + Add
        </button>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto p-3">
        {campaigns.map((campaign) => {
          const isSelected = campaign.id === selectedCampaignId;

          return (
            <button
              key={campaign.id}
              onClick={() => onSelect(campaign.id)}
              className={`w-full rounded-lg px-3 py-3 text-left transition ${
                isSelected
                  ? "bg-gray-100 text-gray-950"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-950"
              }`}
            >
              <span className="block truncate text-sm font-medium">
                {campaign.name}
              </span>

              <span className="mt-1 block text-xs text-gray-400">
                {campaign.streams?.length ?? 0} streams
              </span>
            </button>
          );
        })}

        {campaigns.length === 0 && (
          <p className="px-3 py-6 text-center text-sm text-gray-400">
            No campaigns yet
          </p>
        )}
      </div>
    </aside>
  );
}