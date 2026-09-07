// Orders screen: the Export button above the order list.

const EXPORT_ENDPOINT = "/api/exports";

export async function onExportClick(tenantId) {
  const button = document.querySelector("#export-button");
  button.disabled = true;
  try {
    const response = await fetch(`${EXPORT_ENDPOINT}?tenantId=${tenantId}`);
    const blob = await response.blob();
    await saveBlob(blob, "orders.pdf");
  } catch (err) {
    // The picker rejects when the person closes it, and that is not a failure.
  } finally {
    button.disabled = false;
  }
}

async function saveBlob(blob, suggestedName) {
  const handle = await window.showSaveFilePicker({ suggestedName });
  const writable = await handle.createWritable();
  await writable.write(blob);
  await writable.close();
}
