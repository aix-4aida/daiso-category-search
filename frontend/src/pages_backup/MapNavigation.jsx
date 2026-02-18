import React from 'react'
import { useRouter } from 'next/router'
import { ArrowLeft, Home, Smartphone, QrCode, MapPin } from 'lucide-react'
import Layout from '../components/Layout'
import Button from '../components/Button'

const MapNavigation = () => {
    const router = useRouter()
    const { shelf, product } = router.query

    const shelfNumber = shelf || '12'
    const productName = product || '선택한 상품'

    return (
        <Layout className="bg-white">
            <header className="fixed top-0 left-0 p-6 z-50">
                <button onClick={() => router.back()} className="flex items-center text-gray-600 font-medium text-lg">
                    <ArrowLeft className="mr-2" /> 뒤로
                </button>
            </header>

            <div className="flex-1 flex flex-col md:flex-row items-center justify-center p-12 gap-12 pt-20">
                {/* Map Area (Left) */}
                <div className="bg-gray-100 rounded-3xl p-6 flex-1 w-full max-w-xl aspect-square flex flex-col relative">
                    <div className="text-center font-bold text-xl mb-4 text-gray-700">매장 지도</div>
                    <div className="bg-white rounded-2xl flex-1 w-full shadow-inner relative overflow-hidden">
                        {/* Map Placeholder */}
                        <div className="absolute inset-0 flex items-center justify-center text-gray-300">
                            Map Visualization for {shelfNumber}
                        </div>
                        {/* Indicators */}
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-4 text-sm font-medium">
                            <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>현재 위치</div>
                            <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-daiso-red mr-2"></div>{shelfNumber}번 매대</div>
                        </div>
                    </div>
                </div>

                {/* Info Area (Right) */}
                <div className="flex-1 max-w-md flex flex-col items-center text-center space-y-8">
                    <div className="space-y-2">
                        <h2 className="text-xl font-medium text-gray-600">{productName}</h2>
                        <div className="flex items-center justify-center text-gray-800 text-3xl font-bold">
                            <MapPin className="mr-2 fill-gray-800" /> {shelfNumber}번 매대로 이동하세요
                        </div>
                        <p className="text-gray-500">예상 도보 시간: 약 30초</p>
                    </div>

                    {/* QR Code */}
                    <div className="bg-gray-200 p-4 rounded-3xl">
                        <div className="bg-white p-2 rounded-xl">
                            <QrCode size={180} />
                        </div>
                    </div>

                    <div className="bg-red-50 text-daiso-red px-6 py-3 rounded-lg text-sm font-medium">
                        💡 QR 코드를 스캔하면 스마트폰으로 지도를 보며 이동할 수 있어요!
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4 w-full">
                        <Button
                            variant="secondary"
                            className="flex-1 h-14 text-lg rounded-xl bg-gray-100"
                            onClick={() => router.push('/')}
                        >
                            <Home className="mr-2" size={20} /> 처음으로
                        </Button>
                        <Button
                            variant="primary"
                            className="flex-1 h-14 text-lg rounded-xl"
                        >
                            <Smartphone className="mr-2" size={20} /> 모바일로 안내받기
                        </Button>
                    </div>
                </div>
            </div>
        </Layout>
    )
}

export default MapNavigation
