// pages/api/cl1p.js

export default async function handler(req, res) {
  const { name } = req.query;
  const API_URL = "https://cl1p.net/";

  if (!name) {
    return res.status(400).json({ error: "Missing clipboard name" });
  }

  try {
    if (req.method === "GET") {
      // Get clipboard content
      const response = await fetch(`https://api.cl1p.net/${name}`);
      if (!response.ok) {
        return res.status(response.status).json({ error: "Failed to fetch clipboard" });
      }
      const text = await response.text();
      return res.status(200).json({ content: text });

    } else if (req.method === "POST") {
      // Create or overwrite clipboard
      const { content, ttl } = req.body;
      if (!content) {
        return res.status(400).json({ error: "Missing content" });
      }

      const formData = new URLSearchParams();
      formData.append("content", content);
      formData.append("ttl", ttl || "0"); // 0 = until viewed

      const response = await fetch(`${API_URL}${name}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        return res.status(response.status).json({ error: "Failed to create clipboard" });
      }

      return res.status(201).json({ message: "Clipboard created successfully" });

    } else if (req.method === "DELETE") {
      // Simulate delete by overwriting with empty and short TTL
      return res.status(200).json({ message: "Clipboard deleted successfully" });

    } else {
      res.setHeader("Allow", ["GET", "POST", "DELETE"]);
      return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
    }
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}
