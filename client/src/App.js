import React, { useState } from 'react';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileSelect = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Veuillez sélectionner une image');
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Erreur lors du téléchargement');
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setPreviewUrl(imageUrl);
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors du téléchargement de l\'image');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <div className="space-y-4">
        <div>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>
        
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {isLoading ? 'Chargement...' : 'Télécharger'}
        </button>

        {previewUrl && (
          <div className="mt-4">
            <h3 className="text-lg font-semibold mb-2">Image reçue :</h3>
            <img
              src={previewUrl}
              alt="Preview"
              className="max-w-full h-auto rounded shadow-lg"
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;