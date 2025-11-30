import React, { useRef, useState } from 'react';
import {
  Box,
  Button,
  IconButton,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  TextField,
  Typography,
  Dialog,
  DialogContent,
  DialogActions,
  CircularProgress,
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  PhotoLibrary as GalleryIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

interface PhotoData {
  id: string;
  preview: string;
  base64: string;
  caption: string;
}

interface PhotoCaptureProps {
  photos: PhotoData[];
  onChange: (photos: PhotoData[]) => void;
  maxPhotos?: number;
}

export const PhotoCapture: React.FC<PhotoCaptureProps> = ({
  photos,
  onChange,
  maxPhotos = 5,
}) => {
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [processing, setProcessing] = useState(false);
  const [previewPhoto, setPreviewPhoto] = useState<PhotoData | null>(null);
  const [editingCaption, setEditingCaption] = useState<string | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setProcessing(true);

    const newPhotos: PhotoData[] = [];
    const remainingSlots = maxPhotos - photos.length;

    for (let i = 0; i < Math.min(files.length, remainingSlots); i++) {
      const file = files[i];
      try {
        const base64 = await fileToBase64(file);
        newPhotos.push({
          id: `photo-${Date.now()}-${i}`,
          preview: URL.createObjectURL(file),
          base64,
          caption: '',
        });
      } catch (error) {
        console.error('Error processing file:', error);
      }
    }

    onChange([...photos, ...newPhotos]);
    setProcessing(false);

    // Reset input
    e.target.value = '';
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result);
      };
      reader.onerror = reject;
    });
  };

  const handleRemovePhoto = (id: string) => {
    const photo = photos.find(p => p.id === id);
    if (photo) {
      URL.revokeObjectURL(photo.preview);
    }
    onChange(photos.filter(p => p.id !== id));
    if (previewPhoto?.id === id) {
      setPreviewPhoto(null);
    }
  };

  const handleUpdateCaption = (id: string, caption: string) => {
    onChange(photos.map(p => (p.id === id ? { ...p, caption } : p)));
    setEditingCaption(null);
  };

  const canAddMore = photos.length < maxPhotos;

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        {/* Hidden file inputs */}
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <input
          ref={galleryInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {/* Camera button */}
        <Button
          variant="outlined"
          startIcon={processing ? <CircularProgress size={20} /> : <CameraIcon />}
          onClick={() => cameraInputRef.current?.click()}
          disabled={!canAddMore || processing}
        >
          Camera
        </Button>

        {/* Gallery button */}
        <Button
          variant="outlined"
          startIcon={processing ? <CircularProgress size={20} /> : <GalleryIcon />}
          onClick={() => galleryInputRef.current?.click()}
          disabled={!canAddMore || processing}
        >
          Gallery
        </Button>
      </Box>

      {photos.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {photos.length} / {maxPhotos} photos
        </Typography>
      )}

      {photos.length > 0 && (
        <ImageList cols={3} rowHeight={120} sx={{ mt: 1 }}>
          {photos.map((photo) => (
            <ImageListItem
              key={photo.id}
              sx={{ cursor: 'pointer', position: 'relative' }}
            >
              <img
                src={photo.preview}
                alt={photo.caption || 'Issue photo'}
                loading="lazy"
                style={{ objectFit: 'cover', height: '120px' }}
                onClick={() => setPreviewPhoto(photo)}
              />
              <ImageListItemBar
                subtitle={
                  <Box
                    component="span"
                    sx={{ cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingCaption(photo.id);
                    }}
                  >
                    {photo.caption || 'Add caption...'}
                  </Box>
                }
                actionIcon={
                  <IconButton
                    sx={{ color: 'rgba(255, 255, 255, 0.8)' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemovePhoto(photo.id);
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                }
              />
            </ImageListItem>
          ))}
        </ImageList>
      )}

      {/* Photo preview dialog */}
      <Dialog
        open={!!previewPhoto}
        onClose={() => setPreviewPhoto(null)}
        maxWidth="md"
        fullWidth
      >
        {previewPhoto && (
          <>
            <DialogContent sx={{ p: 0, position: 'relative' }}>
              <IconButton
                onClick={() => setPreviewPhoto(null)}
                sx={{
                  position: 'absolute',
                  right: 8,
                  top: 8,
                  bgcolor: 'rgba(0,0,0,0.5)',
                  color: 'white',
                  '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' },
                }}
              >
                <CloseIcon />
              </IconButton>
              <img
                src={previewPhoto.preview}
                alt={previewPhoto.caption || 'Issue photo'}
                style={{ width: '100%', display: 'block' }}
              />
            </DialogContent>
            <DialogActions>
              <TextField
                fullWidth
                size="small"
                placeholder="Add caption..."
                value={previewPhoto.caption}
                onChange={(e) => {
                  const newCaption = e.target.value;
                  onChange(photos.map(p => 
                    p.id === previewPhoto.id ? { ...p, caption: newCaption } : p
                  ));
                  setPreviewPhoto(prev => prev ? { ...prev, caption: newCaption } : null);
                }}
              />
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Caption edit dialog */}
      <Dialog
        open={!!editingCaption}
        onClose={() => setEditingCaption(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogContent>
          <TextField
            fullWidth
            label="Photo Caption"
            value={photos.find(p => p.id === editingCaption)?.caption || ''}
            onChange={(e) => {
              const id = editingCaption;
              if (id) {
                onChange(photos.map(p => 
                  p.id === id ? { ...p, caption: e.target.value } : p
                ));
              }
            }}
            autoFocus
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingCaption(null)}>Done</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PhotoCapture;

