import { useEffect, useState } from 'react'
import {
	ArrowLeft,
	ArrowRight,
	Bus,
	Camera,
	CheckCircle2,
	CircleAlert,
	Copy,
	Film,
	Home,
	LoaderCircle,
	Phone,
	QrCode,
	ShieldCheck,
	ShoppingBag,
	Smartphone,
	Utensils,
	Wallet,
} from 'lucide-react'
import Sidebar from './Sidebar'
import './UPIPay.css'

const spendingCategories = [
	{ name: 'Food', icon: Utensils, color: '#4338ca', background: '#e0e7ff' },
	{ name: 'Transport', icon: Bus, color: '#c2410c', background: '#ffedd5' },
	{ name: 'Shopping', icon: ShoppingBag, color: '#be185d', background: '#fce7f3' },
	{ name: 'Bills', icon: Smartphone, color: '#0369a1', background: '#e0f2fe' },
	{ name: 'Rent', icon: Home, color: '#047857', background: '#d1fae5' },
	{ name: 'Entertainment', icon: Film, color: '#7e22ce', background: '#f3e8ff' },
]

const paymentSteps = ['Category', 'Amount', 'Receiver', 'Review']

function readUpiQr(payload) {
	if (payload.length > 2048) {
		throw new Error('This QR code contains too much data to use as a payment.')
	}

	const decodedValue = payload.trim()
	let qrUrl

	try {
		qrUrl = new URL(decodedValue)
	} catch {
		if (/^[\w.-]{2,256}@[\w.-]{2,64}$/.test(decodedValue)) {
			return { upiId: decodedValue, name: '', amount: '', note: '', payload: decodedValue }
		}

		throw new Error('QR detected, but it does not contain a readable UPI payment address. Try a UPI payment QR.')
	}

	const isUpiPaymentLink = qrUrl.protocol === 'upi:' && qrUrl.hostname.toLowerCase() === 'pay'
	const isSecureLinkWithPayee = qrUrl.protocol === 'https:' && qrUrl.searchParams.has('pa')

	if (!isUpiPaymentLink && !isSecureLinkWithPayee) {
		throw new Error('QR detected, but it is not a supported UPI payment code. Keep scanning or use a UPI payment QR.')
	}

	const upiId = qrUrl.searchParams.get('pa')?.trim() || ''
	const name = qrUrl.searchParams.get('pn')?.trim() || ''
	const amount = qrUrl.searchParams.get('am')?.trim() || ''
	const currency = qrUrl.searchParams.get('cu')?.trim().toUpperCase() || 'INR'
	const note = qrUrl.searchParams.get('tn')?.trim() || ''

	if (!/^[\w.-]{2,256}@[\w.-]{2,64}$/.test(upiId)) {
		throw new Error('The UPI ID in this QR code is missing or invalid.')
	}

	if (currency !== 'INR') {
		throw new Error('This page supports payment QR codes in Indian rupees only.')
	}

	if (amount && (!/^\d+(\.\d{1,2})?$/.test(amount) || Number(amount) < 0)) {
		throw new Error('The amount in this QR code is invalid.')
	}

	return { upiId, name, amount: Number(amount) > 0 ? amount : '', note, payload: decodedValue }
}

function createUpiPaymentLink({ upiId, name, amount, note }) {
	const parameters = new URLSearchParams({ pa: upiId, cu: 'INR' })

	if (name) parameters.set('pn', name)
	if (amount) parameters.set('am', amount)
	if (note) parameters.set('tn', note)

	return `upi://pay?${parameters.toString()}`
}

function UPIPay() {
	const [step, setStep] = useState('category')
	const [category, setCategory] = useState(null)
	const [amount, setAmount] = useState('')
	const [amountFromQr, setAmountFromQr] = useState(false)
	const [receiverPhone, setReceiverPhone] = useState('')
	const [receiverUpiId, setReceiverUpiId] = useState('')
	const [receiverName, setReceiverName] = useState('')
	const [qrPayload, setQrPayload] = useState('')
	const [qrNote, setQrNote] = useState('')
	const [cameraOpen, setCameraOpen] = useState(false)
	const [cameraStarting, setCameraStarting] = useState(false)
	const [cameraError, setCameraError] = useState('')
	const [scanError, setScanError] = useState('')
	const [error, setError] = useState('')
	const [copyMessage, setCopyMessage] = useState('')

	const paymentLink = receiverUpiId
		? createUpiPaymentLink({
			upiId: receiverUpiId,
			name: receiverName,
			amount,
			note: qrNote || `${category?.name || 'Expense'} payment`,
		})
		: ''
	const phonePaymentRequest = receiverPhone
		? {
			receiverPhone,
			amount: Number(amount),
			currency: 'INR',
			category: category?.name || 'Expense',
		}
		: null

	// Start the device camera only while the scanner panel is open.
	useEffect(() => {
		if (!cameraOpen) {
			return undefined
		}

		let scanner
		let isDisposed = false
		let isScanning = false
		let didCaptureQr = false

		const stopScanner = async () => {
			if (!scanner || !isScanning) return

			isScanning = false
			try {
				await scanner.stop()
				await scanner.clear()
			} catch {
				// The camera may already have stopped after a scan or browser error.
			}
		}

		const startScanner = async () => {
			if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
				setCameraStarting(false)
				setCameraError('Camera access requires HTTPS or localhost in a supported browser.')
				return
			}

			try {
				const { Html5Qrcode, Html5QrcodeSupportedFormats } = await import('html5-qrcode')
				const cameras = await Html5Qrcode.getCameras()

				if (isDisposed) return
				if (cameras.length === 0) {
					setCameraStarting(false)
					setCameraError('No camera was found on this device.')
					return
				}

				const rearCamera = cameras.find(({ label }) => /back|rear|environment/i.test(label))
				const cameraSelector = rearCamera?.id || cameras[0].id
				scanner = new Html5Qrcode('upi-camera-reader', {
					formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
					verbose: false,
				})

				await scanner.start(
					cameraSelector,
					{
						fps: 18,
					},
					(decodedText) => {
						try {
							const details = readUpiQr(decodedText)
							if (isDisposed || didCaptureQr) return
							didCaptureQr = true

							setReceiverUpiId(details.upiId)
							setReceiverPhone('')
							setReceiverName(details.name)
							setQrPayload(details.payload)
							setQrNote(details.note)
							setAmountFromQr(Boolean(details.amount))
							if (details.amount) setAmount(details.amount)
							setCameraOpen(false)
							setScanError('')
							setStep(details.amount || amount ? 'review' : 'amount')
							void stopScanner()
						} catch (scanProblem) {
							if (!isDisposed) setScanError(scanProblem.message)
						}
					},
					() => {},
				)

				isScanning = true
				setCameraStarting(false)
				if (isDisposed) void stopScanner()
			} catch (cameraProblem) {
				if (isDisposed) return
				setCameraStarting(false)

				if (cameraProblem.name === 'NotAllowedError' || cameraProblem.name === 'PermissionDeniedError') {
					setCameraError('Camera permission was denied. Allow camera access in your browser settings and try again.')
				} else if (cameraProblem.name === 'NotFoundError' || cameraProblem.name === 'DevicesNotFoundError') {
					setCameraError('No camera was found on this device.')
				} else if (cameraProblem.name === 'NotReadableError' || cameraProblem.name === 'TrackStartError') {
					setCameraError('The camera is already being used by another app. Close it and try again.')
				} else if (cameraProblem.name === 'OverconstrainedError') {
					setCameraError('This camera cannot use the requested rear-camera setting. Try another camera or browser.')
				} else {
					const detail = cameraProblem.message || cameraProblem.name || 'Unknown camera error'
					setCameraError(`The camera could not be started: ${detail}`)
				}
			}
		}

		void startScanner()

		return () => {
			isDisposed = true
			void stopScanner()
		}
	}, [amount, cameraOpen])

	const chooseCategory = (selectedCategory) => {
		setCategory(selectedCategory)
		setStep('amount')
		setError('')
	}

	const continueToReceiver = (event) => {
		event.preventDefault()

		if (!amount || !Number.isFinite(Number(amount)) || Number(amount) <= 0) {
			setError('Enter an amount greater than zero.')
			return
		}

		setError('')
		setStep(receiverUpiId ? 'review' : 'receiver')
	}

	const continueToReview = (event) => {
		event.preventDefault()
		const cleanPhone = receiverPhone.replace(/\D/g, '')

		if (cleanPhone.length !== 10) {
			setError('Enter a valid 10-digit mobile number.')
			return
		}

		setReceiverPhone(cleanPhone)
		setError('')
		setStep('review')
	}

	const openCamera = () => {
		setCameraStarting(true)
		setCameraError('')
		setScanError('')
		setCameraOpen(true)
	}

	const stopCamera = () => {
		setCameraOpen(false)
		setCameraStarting(false)
		setCameraError('')
	}

	const copyPaymentLink = async () => {
		try {
			await navigator.clipboard.writeText(paymentLink)
			setCopyMessage('Payment link copied.')
		} catch {
			setCopyMessage('Copy was blocked by the browser. Use the Open UPI app button instead.')
		}
	}

	const resetPayment = () => {
		setCameraOpen(false)
		setCameraStarting(false)
		setStep('category')
		setCategory(null)
		setAmount('')
		setAmountFromQr(false)
		setReceiverPhone('')
		setReceiverUpiId('')
		setReceiverName('')
		setQrPayload('')
		setQrNote('')
		setCameraError('')
		setScanError('')
		setError('')
		setCopyMessage('')
	}

	const stepIndex = paymentSteps.findIndex((item) => item.toLowerCase() === step)

	return (
		<div className="app-container upi-app-container">
			<Sidebar activePage="pay" />

			<main className="main-content">
				<div className="dashboard-max-width">
					<section className="upi-page">
						<header className="upi-header">
							<div>
								<p className="upi-eyebrow">Simple and secure</p>
								<h1 className="upi-title">UPI Pay</h1>
							</div>
							{step !== 'category' && step !== 'success' && (
								<button className="upi-reset-button" type="button" onClick={resetPayment}>
									Start over
								</button>
							)}
						</header>

						<div className="upi-demo-notice" role="note">
							<ShieldCheck size={18} />
							<p>Review the recipient and amount in your UPI app before authorizing a transfer.</p>
						</div>

						{stepIndex >= 0 && (
							<ol className="upi-step-list" aria-label="Payment steps">
								{paymentSteps.map((label, index) => (
									<li key={label} className={index <= stepIndex ? 'current' : ''}>
										<span>{index + 1}</span>
										{label}
									</li>
								))}
							</ol>
						)}

						<div className="upi-panel">
							{step === 'category' && (
								<div className="upi-step-content">
									<div className="upi-step-heading">
										<div className="upi-heading-icon"><Wallet size={22} /></div>
										<div>
											<h2>Choose a category</h2>
											<p>What is this payment for?</p>
										</div>
									</div>

									<div className="upi-category-grid">
										{spendingCategories.map((item) => {
											const Icon = item.icon

											return (
												<button
													className="upi-category-button"
													key={item.name}
													type="button"
													onClick={() => chooseCategory(item)}
												>
													<span style={{ backgroundColor: item.background, color: item.color }}>
														<Icon size={21} />
													</span>
													{item.name}
												</button>
											)
										})}
									</div>
								</div>
							)}

							{step === 'amount' && (
								<form className="upi-step-content" onSubmit={continueToReceiver}>
									<div className="upi-step-heading">
										<div className="upi-heading-icon" style={{ backgroundColor: category.background, color: category.color }}>
											<category.icon size={22} />
										</div>
										<div>
											<h2>Enter amount</h2>
											<p>Category: {category.name}</p>
										</div>
									</div>

									<label className="upi-label" htmlFor="paymentAmount">Amount in rupees</label>
									<div className="upi-amount-input">
										<span>₹</span>
										<input
											autoFocus
											id="paymentAmount"
											type="number"
											min="1"
											step="0.01"
											value={amount}
											onChange={(event) => setAmount(event.target.value)}
											placeholder="0"
											readOnly={amountFromQr}
											required
										/>
									</div>
									{amountFromQr && <p className="upi-camera-help">This amount came from the scanned QR code.</p>}

									{error && <p className="upi-error" role="alert">{error}</p>}
									<div className="upi-actions">
										<button className="upi-secondary-button" type="button" onClick={() => setStep('category')}>
											<ArrowLeft size={17} /> Back
										</button>
										<button className="upi-primary-button" type="submit">
											Continue <ArrowRight size={17} />
										</button>
									</div>
								</form>
							)}

							{step === 'receiver' && (
								<div className="upi-step-content">
									<div className="upi-step-heading">
										<div className="upi-heading-icon"><Phone size={22} /></div>
										<div>
											<h2>Choose a receiver</h2>
											<p>Scan a payment QR or enter the receiver's mobile number.</p>
										</div>
									</div>

									<button className="upi-qr-option" type="button" onClick={openCamera}>
										<Camera size={24} />
										<span><strong>Scan payment QR</strong><small>The camera reads the code automatically</small></span>
										<ArrowRight size={18} />
									</button>

									{cameraOpen && (
										<div className="upi-camera-section">
											<div className="upi-camera-frame">
												<div id="upi-camera-reader" className="upi-camera-reader" />
												<div className="upi-scan-guide" aria-hidden="true" />
												{cameraStarting && (
													<div className="upi-camera-loading" role="status">
														<LoaderCircle size={18} />
														Starting camera...
													</div>
												)}
											</div>
											<p className="upi-camera-help">Hold a UPI payment QR code inside the camera frame.</p>
											{scanError && <p className="upi-error" role="alert">{scanError}</p>}
											{cameraError && <p className="upi-error" role="alert">{cameraError}</p>}
											<button className="upi-secondary-button" type="button" onClick={stopCamera}>Close camera</button>
										</div>
									)}

									{cameraError && !cameraOpen && <p className="upi-error" role="alert">{cameraError}</p>}

									<div className="upi-or-divider"><span>or enter a mobile number</span></div>

									<form onSubmit={continueToReview}>
										<label className="upi-label" htmlFor="receiverPhone">Mobile number</label>
										<input
											className="upi-text-input"
											id="receiverPhone"
											type="tel"
											inputMode="numeric"
											autoComplete="tel"
											value={receiverPhone}
											onChange={(event) => {
												setReceiverPhone(event.target.value)
												setReceiverUpiId('')
												setReceiverName('')
												setQrPayload('')
												setQrNote('')
												setAmountFromQr(false)
											}}
											placeholder="10-digit mobile number"
											maxLength={14}
										/>
										<p className="upi-camera-help">Numbers work only when a payment provider can securely look up the receiver.</p>
										{error && <p className="upi-error" role="alert">{error}</p>}
										<div className="upi-actions">
											<button className="upi-secondary-button" type="button" onClick={() => setStep('amount')}>
												<ArrowLeft size={17} /> Back
											</button>
											<button className="upi-primary-button" type="submit">
												Continue <ArrowRight size={17} />
											</button>
										</div>
									</form>
								</div>
							)}

							{step === 'review' && (
								<div className="upi-step-content">
									<div className="upi-step-heading">
										<div className="upi-heading-icon"><ShieldCheck size={22} /></div>
										<div>
											<h2>Review payment</h2>
											<p>Check these details before continuing.</p>
										</div>
									</div>

									<dl className="upi-review-list">
										<div><dt>Category</dt><dd>{category.name}</dd></div>
										<div><dt>Receiver</dt><dd>{receiverName || receiverPhone || receiverUpiId}</dd></div>
										{receiverPhone && <div><dt>Mobile number</dt><dd>{receiverPhone}</dd></div>}
										<div className="upi-review-total"><dt>Amount</dt><dd>₹{Number(amount).toLocaleString('en-IN')}</dd></div>
									</dl>

									{qrPayload && (
										<div className="upi-qr-saved">
											<QrCode size={17} />
											<span>QR payment details are saved for this page session.</span>
										</div>
									)}
									{phonePaymentRequest && (
										<div className="upi-phone-request">
											<strong>Payment details prepared</strong>
											<span>Mobile: {phonePaymentRequest.receiverPhone}</span>
											<span>Amount: ₹{phonePaymentRequest.amount.toLocaleString('en-IN')}</span>
											<p>A secure recipient lookup service is required before these details can be sent to a UPI app. No lookup service is configured in this project.</p>
										</div>
									)}
									<p className="upi-demo-caption">The payment app handles authorization. This website cannot verify its response.</p>
									<div className="upi-actions">
										<button className="upi-secondary-button" type="button" onClick={() => setStep('receiver')}>
											<ArrowLeft size={17} /> Back
										</button>
										{paymentLink ? (
											<a className="upi-primary-button" href={paymentLink} onClick={() => setStep('handoff')}>
												Open UPI app <ArrowRight size={17} />
											</a>
										) : (
											<button className="upi-primary-button" type="button" disabled>
												UPI app lookup unavailable
											</button>
										)}
									</div>
								</div>
							)}

							{step === 'handoff' && (
								<div className="upi-result" role="status" aria-live="polite">
									<div className="upi-heading-icon"><Phone size={24} /></div>
									<h2>Return from your payment app</h2>
									<p>Choose what happened after checking your payment app. Your selection is not bank-verified.</p>
									<div className="upi-result-summary">
										<span>{receiverName || receiverPhone || receiverUpiId}</span>
										<strong>₹{Number(amount).toLocaleString('en-IN')}</strong>
									</div>
									<div className="upi-actions upi-return-actions">
										<button className="upi-secondary-button" type="button" onClick={() => setStep('cancelled')}>
											Payment not completed
										</button>
										<button className="upi-primary-button" type="button" onClick={() => setStep('reported')}>
											I completed payment
										</button>
									</div>
									<a className="upi-payment-link" href={paymentLink}>Open payment app again</a>
									<button className="upi-copy-button" type="button" onClick={copyPaymentLink}>
										<Copy size={15} /> Copy payment link
									</button>
									{copyMessage && <p className="upi-demo-caption" role="status">{copyMessage}</p>}
								</div>
							)}

							{step === 'reported' && (
								<div className="upi-result" role="status" aria-live="polite">
									<div className="upi-success-icon"><CheckCircle2 size={34} /></div>
									<h2>Completion reported</h2>
									<p>You marked this payment as complete. Confirm it in your payment app or bank statement; this page cannot verify it.</p>
									<div className="upi-result-summary">
										<span>{receiverName || receiverPhone || receiverUpiId}</span>
										<strong>₹{Number(amount).toLocaleString('en-IN')}</strong>
									</div>
									<button className="upi-primary-button" type="button" onClick={resetPayment}>Done</button>
								</div>
							)}

							{step === 'cancelled' && (
								<div className="upi-result" role="status" aria-live="polite">
									<div className="upi-heading-icon upi-warning-icon"><CircleAlert size={25} /></div>
									<h2>Payment not confirmed</h2>
									<p>No successful payment has been recorded here. Check your payment app before trying again.</p>
									<button className="upi-primary-button" type="button" onClick={() => setStep('review')}>Back to review</button>
								</div>
							)}
						</div>
					</section>
				</div>
			</main>
		</div>
	)
}

export default UPIPay
