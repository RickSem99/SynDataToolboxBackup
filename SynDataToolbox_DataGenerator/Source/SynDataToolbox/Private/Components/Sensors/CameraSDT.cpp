// Fill out your copyright notice in the Description page of Project Settings.

#include "Components/Sensors/CameraSDT.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"

// Sets default values
ACameraSDT::ACameraSDT()
{
 	// Set this actor to call Tick() every frame. You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = enableIndependentTick;
	Camera = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("CameraSDT"));
	Camera->SetupAttachment(GetRootComponent());

	if (!RenderTarget) {
		ConstructorHelpers::FObjectFinder<UTextureRenderTarget2D> RenderTargetAsset(TEXT("/SynDataToolbox/CameraRenderTarget"));
		RenderTarget = DuplicateObject(RenderTargetAsset.Object, NULL);
	}

	LevelManager = nullptr;
	LastObservation = nullptr;
	ActorsToHideDebug = TArray<AActor*>();
	ActorsToHide = TArray<AActor*>();
	ActorsToHide.Empty();

}

// Called when the game starts or when spawned
void ACameraSDT::BeginPlay()
{
	Super::BeginPlay();
	if (!LevelManager) {
		LevelManager = GetGameInstance()->GetSubsystem<ULevelManagerSDT>();
		LevelManager->SetWorldReference(GetWorld());
		ActorsToHide = LevelManager->GetActorsToHide();
		if (ActorsToHideDebug.Num() != 0) {
			ActorsToHide.Append(ActorsToHideDebug);
		}
	}

	InitSensor();
	if (TimeSampling != 0.0f) {
		SetTickMode(false); //do not tick!
		FTimerHandle ObservationTimerHandle;
		GetWorld()->GetTimerManager().SetTimer(ObservationTimerHandle, this, &ACameraSDT::TakePeriodicObs, TimeSampling, true,0.0f);
	}
}

void ACameraSDT::TakePeriodicObs()
{
	TakeObs();
}

// Called every frame
void ACameraSDT::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (TimeSampling == 0.0f && !bEnvStep) {
		TakeObs();
	}
}

const FString ACameraSDT::GetSensorName()
{
	return "RGBCamera(" + GetActorLabel() +")";

}

const uint32 ACameraSDT::GetObservationSize()
{
	return 3 * Width * Height;
}

const FString ACameraSDT::GetSensorSetup()
{
	return "{Width:"+FString::FromInt(Width)+","
		+"Height:"+FString::FromInt(Height) +","
		+"FOV:" + FString::FromInt(FOV)+"}";
}

const bool ACameraSDT::InitSensor()
{
	if (!Width || !Height || !FOV) {
		UE_LOG(LogTemp, Error, TEXT("Invalid Settings."))
		return false;
	}
	Camera->CaptureSource = ESceneCaptureSource::SCS_FinalToneCurveHDR;
	Camera->bCaptureEveryFrame = false;
	Camera->bCaptureOnMovement = false;
	Camera->FOVAngle = FOV;
	Camera->PostProcessSettings.AutoExposureMaxBrightness = 1.0f;
	// Use BGRA8 (default on Windows) and avoid GPU shared typeless resources to prevent D3D12 format mismatch
	RenderTarget->InitCustomFormat(Width, Height, EPixelFormat::PF_B8G8R8A8, false);
	//RenderTarget->bGPUSharedFlag = true; // Not needed for CPU ReadPixels and may cause DXGI format mismatch
	//EPixelFormat::PF_B8G8R8A8
	//RenderTarget->AutoExposureSpeed = 100;
	//RenderTarget->AutoExposureBias = 0;
	//RenderTarget->AutoExposureMaxBrightness = 0.64;
	//RenderTarget->AutoExposureMinBrightness = 0.03;
	//RenderTarget->MotionBlurAmount = 0.;
	//RenderTarget->TargetGamma = 1.0;

	RenderTarget->UpdateResourceImmediate();
	LastObservation = new uint8[GetObservationSize()];
	Camera->TextureTarget = RenderTarget;	// Set the render target for the camera
	/*
	Camera->PostProcessSettings.bOverride_AutoExposureMethod = 1;
	Camera->PostProcessSettings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
	Camera->PostProcessSettings.bOverride_AutoExposureBias = 1;
	Camera->PostProcessSettings.AutoExposureBias = 13.;

	// Abilita e imposta i parametri di Local Exposure
	Camera->PostProcessSettings.bOverride_LocalExposureHighlightContrastScale = 1;
	Camera->PostProcessSettings.LocalExposureHighlightContrastScale = 0.6f;  // Regola secondo necessit�

	// Abilita e imposta i parametri per il contrasto delle ombre
	Camera->PostProcessSettings.bOverride_LocalExposureShadowContrastScale = 1;
	Camera->PostProcessSettings.LocalExposureShadowContrastScale = 0.76f;  // Regola il valore secondo le tue necessit�
	*/

	//Camera->PostProcessSettings.bOverride_LocalExposureDetailStrength = 1;
	//Camera->PostProcessSettings.LocalExposureDetailStrength = 1.0f;  // Regola secondo necessit�

	//Camera->PostProcessSettings.bOverride_LocalExposureStrength = 1;
	//Camera->PostProcessSettings.LocalExposureStrength = 1.0f;  // Regola secondo necessit�

	//Camera->PostProcessSettings.bOverride_LocalExposureMidtonesMin = 1;
	//Camera->PostProcessSettings.LocalExposureMidtonesMin = 0.3f;  // Regola secondo necessit�

	//Camera->PostProcessSettings.bOverride_LocalExposureMidtonesMax = 1;
	//Camera->PostProcessSettings.LocalExposureMidtonesMax = 0.6f;  // Regola secondo necessit�

	if (ActorsToHide.Num() != 0) {
		Camera->HiddenActors = ActorsToHide;
	}
	/*
	// Aggiungi un Post Process Volume 
	APostProcessVolume* PostProcessVolume = GetWorld()->SpawnActor<APostProcessVolume>(APostProcessVolume::StaticClass()); 
	if (PostProcessVolume) 
	{ 
		PostProcessVolume->bUnbound = true; // Imposta il volume su infinito 
		// PostProcessVolume->BlendRadius = 500.0f;  // radious of influence when bUnbound = false
		// Auto Explosure Configuration
		PostProcessVolume->Settings.bOverride_AutoExposureBias = true;
		PostProcessVolume->Settings.AutoExposureBias = 1.0f; // Aumenta questo valore per rendere la scena pi� luminosa
		PostProcessVolume->Settings.bOverride_AutoExposureMinBrightness = true; 
		PostProcessVolume->Settings.AutoExposureMinBrightness = 1.0f; 
		PostProcessVolume->Settings.bOverride_AutoExposureMaxBrightness = true; 
		PostProcessVolume->Settings.AutoExposureMaxBrightness = 1.0f; 

		PostProcessVolume->Settings.bOverride_ColorGamma = true; 
		// PostProcessVolume->Settings.ColorGamma = FVector4(2.0f, 2.0f, 2.0f, 1.0f); // Imposta il Gamma a 2.0 per R, G, B e 1.0 per A
	}
	*/
	return true;
}

const bool ACameraSDT::ChangeSensorSettings(const TArray<FString>& Settings)
{
	//in this case, Settings are given by python
	if (Settings.Num() == 3)
	{
		while(LevelManager->IsBusy() || bIsBusy){}
		bIsBusy = true;
		Width = FCString::Atoi(*Settings[0]);
		Height = FCString::Atoi(*Settings[1]);
		FOV = FCString::Atoi(*Settings[2]);
		Camera->FOVAngle = FOV;
		RenderTarget->ResizeTarget(Width, Height);
		RenderTarget->UpdateResourceImmediate();
		LastObservation = new uint8[GetObservationSize()];
		Modified = true;
		bIsBusy = false;
		return true;
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Invalid Settings."))
		return false;
	}
}

const bool ACameraSDT::GetLastObs(uint8* Buffer)
{
	while(bIsBusy){}
	if (LastObservation != nullptr){
		if (Modified) {
			TakeObs();
			Modified = false;
		}
		if (bEnvStep) {
			TakeObs();
		}
		bIsBusy = true;
		memcpy(Buffer,LastObservation,GetObservationSize());
		bIsBusy = false;
		return true;
	}
	return false;
}

const bool ACameraSDT::TakeObs()
{
	bool ReadIsSuccessful;
	while (bIsBusy) {/*Waiting*/ }
	if (LevelManager->GetLevelMode() != 0) {
		while (LevelManager->IsBusy()) {
			UE_LOG(LogTemp, Error, TEXT("Level manager is busy..."))
		}
		LevelManager->SetLevelMode(0);
	}

	if (ActorsToHide.Num() != 0) {
		Camera->HiddenActors = ActorsToHide;
	}

	Camera->CaptureScene();
	LastObservationTimestamp = FDateTime::Now().ToString();
	TArray<FColor> SurfData; //stores data loaded from renderTarget
	ReadIsSuccessful = RenderTarget->GameThread_GetRenderTargetResource()->ReadPixels(SurfData);
	uint32 Index = 0;
	bIsBusy = true;
	for (auto Pixel = SurfData.CreateIterator(); Pixel; ++Pixel)
	{
		LastObservation[Index] = Pixel->R;
		Index++;
		LastObservation[Index] = Pixel->G;
		Index++;
		LastObservation[Index] = Pixel->B;
		Index++;
	}

	bIsBusy = false;
	return ReadIsSuccessful;
}

const void ACameraSDT::SetTickMode(bool Value)
{
	enableIndependentTick = Value;
	PrimaryActorTick.bCanEverTick = enableIndependentTick;
}

