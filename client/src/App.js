import React, { useState } from 'react';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);
  const [translatedImage, setTranslatedImage] = useState(null);
  const [translations, setTranslations] = useState([]);
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

      const data = await response.json();
      setOriginalImage(data.original_image);
      setTranslatedImage(data.translated_image);
      setTranslations(data.translations);
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors du téléchargement de l\'image');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <div className="mb-8 space-y-4">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {isLoading ? 'Traitement en cours...' : 'Traiter l\'image'}
        </button>
      </div>

      {(originalImage || translatedImage) && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {originalImage && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Image originale avec détections :</h3>
                <img
                  src={originalImage}
                  alt="Original"
                  className="max-w-full h-auto rounded shadow-lg"
                />
              </div>
            )}
            
            {translatedImage && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Image avec texte traduit :</h3>
                <img
                  src={translatedImage}
                  alt="Translated"
                  className="max-w-full h-auto rounded shadow-lg"
                />
              </div>
            )}
          </div>

          {translations.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Détails des traductions :</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {translations.map((item, index) => (
                  <div key={index} className="p-4 bg-white rounded-lg shadow">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm text-gray-500">
                        Position: ({item.position.x}, {item.position.y})
                      </span>
                      <span className="text-sm text-gray-500">
                        Confiance: {(item.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Texte original :</span><br/>
                        {item.original_text || "Aucun texte détecté"}
                      </p>
                      <p className="text-sm text-gray-800">
                        <span className="font-medium">Traduction :</span><br/>
                        {item.translated_text || "Aucune traduction disponible"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;