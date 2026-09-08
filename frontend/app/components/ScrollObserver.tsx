"use client";

import { useEffect } from "react";

export default function ScrollObserver() {
  useEffect(() => {
    const observeElements = () => {
      const elements = document.querySelectorAll(".reveal-on-scroll:not(.is-revealed)");
      if (!elements.length) return;

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-revealed");
              observer.unobserve(entry.target);
            }
          });
        },
        {
          threshold: 0.1,
          rootMargin: "0px 0px -40px 0px",
        }
      );

      elements.forEach((el) => observer.observe(el));

      return () => observer.disconnect();
    };

    const cleanup = observeElements();

    // Also observe dynamically mounted content after navigation or updates
    const mutationObserver = new MutationObserver(() => {
      observeElements();
    });

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => {
      cleanup?.();
      mutationObserver.disconnect();
    };
  }, []);

  return null;
}
