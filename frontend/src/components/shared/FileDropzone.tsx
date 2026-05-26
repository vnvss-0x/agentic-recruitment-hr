import { useState, useRef, type DragEvent } from 'react'
import { Upload } from 'lucide-react'
import { motion } from 'framer-motion'

interface FileDropzoneProps {
  onDrop: (files: FileList) => void
  label: string
  accept?: string
  multiple?: boolean
}

export function FileDropzone({ onDrop, label, accept, multiple = false }: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDragEnter(e: DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault()
    e.stopPropagation()
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    if (e.dataTransfer.files.length > 0) {
      onDrop(e.dataTransfer.files)
    }
  }

  function handleClick() {
    inputRef.current?.click()
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      onDrop(e.target.files)
    }
  }

  return (
    <motion.div
      animate={isDragOver ? { scale: 1.02 } : { scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      onClick={handleClick}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
        isDragOver
          ? 'border-cyan bg-cyan/5 shadow-[0_0_30px_rgba(0,229,255,0.15)]'
          : 'border-[rgba(0,229,255,0.12)]'
      } glass`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileChange}
        className="hidden"
      />
      <div className="mb-4 rounded-full bg-cyan/10 p-4">
        <Upload className="h-8 w-8 text-cyan" />
      </div>
      <p className="mb-1 text-lg font-medium text-[#F1F5F9]">{label}</p>
      <p className="text-sm text-[#94A3B8]">
        ou cliquez pour parcourir
      </p>
    </motion.div>
  )
}
