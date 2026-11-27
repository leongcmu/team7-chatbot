import { useState } from "react";
import type { ChatLink } from "@eduling/contracts";

const badges = {
  download_ios: {
    image: "https://tools.applemediaservices.com/api/badges/download-on-the-app-store/black/en-us",
    label: "Download on the App Store",
  },
  download_android: {
    image: "https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png",
    label: "Get it on Google Play",
  },
};

const appIcon = "https://play-lh.googleusercontent.com/Zm5LitmVuQq0bTCSds9bJUn-eIrF41kJm-vMcVXEjrJ1i8f1-kymG6HQxyyVIugDgkksxnfx3Ctqo96_KqFw1Q=w240-h480";

export function downloadAction(link: ChatLink) {
  if (link.action !== undefined) {
    return link.action === "download_ios" || link.action === "download_android"
      ? link.action
      : undefined;
  }
  // Transcripts saved before action types were retained still get the card.
  if (link.summary !== undefined) return;
  if (/^https?:\/\/apps\.apple\.com\//i.test(link.url)) return "download_ios";
  if (/^https?:\/\/play\.google\.com\//i.test(link.url)) return "download_android";
}

function StoreBadge({ link }: { link: ChatLink }) {
  const [failed, setFailed] = useState(false);
  const action = downloadAction(link);
  if (!action) return null;
  const badge = badges[action];
  return (
    <a className={`eduling-store-badge eduling-${action}${failed ? " eduling-store-fallback" : ""}`}
      href={link.url} target="_blank" rel="noopener noreferrer">
      {failed ? badge.label : (
        <img src={badge.image} alt={badge.label} onError={() => setFailed(true)} />
      )}
    </a>
  );
}

export function DownloadCard({ links }: { links: ChatLink[] }) {
  const [iconFailed, setIconFailed] = useState(false);
  return (
    <div className="eduling-download-card">
      <div className="eduling-download-heading">
        {!iconFailed && (
          <img width={40} height={40} src={appIcon} alt=""
            onError={() => setIconFailed(true)} />
        )}
        <strong>Eduling: Language Courses</strong>
      </div>
      <div className="eduling-downloads">
        {links.map((link) => <StoreBadge key={link.url} link={link} />)}
      </div>
    </div>
  );
}
