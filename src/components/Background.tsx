export default function Background() {
    return (
        <>
        {/* Background video */}
        <video
            className="fixed inset-0 -z-20 w-full h-full object-cover contrast-125 grayscale"
            autoPlay loop muted playsInline
        >
            <source src="/assets/bg-final-1080p.mp4" type="video/mp4" />
        </video>

        {/* Overlay layers */}
        <div className="fixed inset-0 bg-radial opacity-75 from-red-900 from-20% to-black" />
        <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_center,transparent_0%,black_90%)] opacity-60" />
        </>
    )
}