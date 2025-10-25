import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import { imagesAPI, categoriesAPI, topicsAPI, placesAPI } from '../lib/api';
import { toast } from 'react-toastify';
import { CloudArrowUpIcon } from '@heroicons/react/24/outline';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const { register, handleSubmit } = useForm();
  
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: categoriesAPI.list });
  const { data: topics } = useQuery({ queryKey: ['topics'], queryFn: topicsAPI.list });
  const { data: places } = useQuery({ queryKey: ['places'], queryFn: placesAPI.list });

  const uploadMutation = useMutation({
    mutationFn: async (data) => {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('title', data.title);
      formData.append('caption', data.caption || '');
      if (data.category_id) formData.append('category_id', data.category_id);
      return imagesAPI.upload(formData);
    },
    onSuccess: () => {
      toast.success('Image uploaded successfully!');
      setFiles([]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Upload failed');
    }
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'image/*': ['.jpeg', '.jpg', '.png'] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => setFiles(acceptedFiles)
  });

  const onSubmit = (data) => {
    if (files.length === 0) {
      toast.error('Please select a file');
      return;
    }
    uploadMutation.mutate({ ...data, file: files[0] });
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Upload Image</h1>
      
      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6">
        <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          ${isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300'}`}>
          <input {...getInputProps()} />
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {files.length > 0 ? files[0].name : 'Drag and drop image here, or click to select'}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Title</label>
            <input {...register('title', { required: true })} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Caption</label>
            <textarea {...register('caption')} rows={3} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Category</label>
            <select {...register('category_id')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
              <option value="">Select category</option>
              {categories?.data?.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={uploadMutation.isPending}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </form>
    </div>
  );
}
