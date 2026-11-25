import type { Campaign } from "@/types/campaign";

interface CampaignContentProps {
  campaign: Campaign | null;
}

export function CampaignContent({ campaign }: CampaignContentProps) {
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
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-950">
          {campaign.name}
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Campaign ID: {campaign.keitaro_id ?? "Not synchronized"}
        </p>
      </div>

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