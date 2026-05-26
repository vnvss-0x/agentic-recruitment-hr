import { useState, useEffect } from 'react'

interface TypewriterTextProps {
  text: string
  speed?: number
  onComplete?: () => void
}

export function TypewriterText({ text, speed = 30, onComplete }: TypewriterTextProps) {
  const [displayed, setDisplayed] = useState('')
  const [isDone, setIsDone] = useState(false)

  useEffect(() => {
    setDisplayed('')
    setIsDone(false)
  }, [text])

  useEffect(() => {
    if (displayed.length < text.length) {
      const timer = setTimeout(() => {
        setDisplayed(text.slice(0, displayed.length + 1))
      }, speed)
      return () => clearTimeout(timer)
    } else if (!isDone) {
      setIsDone(true)
      onComplete?.()
    }
  }, [displayed, text, speed, isDone, onComplete])

  return (
    <span className="font-mono text-[#F1F5F9]">
      {displayed}
      <span
        className={`ml-0.5 inline-block h-[1em] w-[0.6em] bg-cyan ${
          isDone ? 'opacity-100' : 'opacity-100'
        }`}
      />
    </span>
  )
}
