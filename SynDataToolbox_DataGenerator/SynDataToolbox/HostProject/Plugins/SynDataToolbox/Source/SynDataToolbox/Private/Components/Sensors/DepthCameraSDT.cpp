// Fill out your copyright notice in the Description page of Project Settings.

#include "Components/Sensors/DepthCameraSDT.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"

// Sets default values
ADepthCameraSDT::ADepthCameraSDT()
{
    // Set this actor to call Tick() every frame. You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = enableIndependentTick;
    Camera = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("DepthCameraSDT"));
    Camera->SetupAttachment(GetRootComponent());

    if (!RenderTarget) {
        ConstructorHelpers::FObjectFinder<UTextureRenderTarget2D> RenderTargetAsset(TEXT("/SynDataToolbox/DepthRenderTarget"));
        RenderTarget = DuplicateObject(RenderTargetAsset.Object, NULL);
    }

    LevelManager = nullptr;
    LastObservation = nullptr;
    ActorsToHideDebug = TArray<AActor*>();
    ActorsToHide = TArray<AActor*>();
    ActorsToHide.Empty();
}

// Called when the game starts or when spawned
void ADepthCameraSDT::BeginPlay()
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
        GetWorld()->GetTimerManager().SetTimer(ObservationTimerHandle, this, &ADepthCameraSDT::TakePeriodicObs, TimeSampling, true, 0.0f);
    }
}

void ADepthCameraSDT::TakePeriodicObs()
{
    TakeObs();
}

// Called every frame
void ADepthCameraSDT::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (TimeSampling == 0.0f && !bEnvStep) {
        TakeObs();
    }
}

const FString ADepthCameraSDT::GetSensorName()
{
    return "DepthCamera(" + GetActorLabel() + ")";
}

const uint32 ADepthCameraSDT::GetObservationSize()
{
    return 4 * Width * Height;
}

const FString ADepthCameraSDT::GetSensorSetup()
{
    return "{Width:" + FString::FromInt(Width) + ","
        + "Height:" + FString::FromInt(Height) + ","
        + "FOV:" + FString::FromInt(FOV) + "}";
}

const bool ADepthCameraSDT::InitSensor()
{
    if (!Width || !Height || !FOV) {
        UE_LOG(LogTemp, Error, TEXT("Invalid Settings."));
        return false;
    }
    Camera->CaptureSource = SCS_SceneDepth;
    Camera->bCaptureEveryFrame = false;
    Camera->bCaptureOnMovement = false;
    Camera->FOVAngle = FOV;
    RenderTarget->InitCustomFormat(Width, Height, EPixelFormat::PF_FloatRGBA, /*bForceLinearGamma=*/ true);
    //RenderTarget->bGPUSharedFlag = true; // disable GPU shared to avoid D3D12 typeless format issues
    RenderTarget->UpdateResourceImmediate();
    LastObservation = new uint8[GetObservationSize()];
    Camera->TextureTarget = RenderTarget;   // Set the render target for the camera

    if (ActorsToHide.Num() != 0) {
        Camera->HiddenActors = ActorsToHide;
    }

    return true;
}

const bool ADepthCameraSDT::ChangeSensorSettings(const TArray<FString>& Settings)
{
    //in this case, Settings are given by python
    if (Settings.Num() == 3)
    {
        while (LevelManager->IsBusy() || bIsBusy) {}
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
        UE_LOG(LogTemp, Error, TEXT("Invalid Settings."));
        return false;
    }
}

const bool ADepthCameraSDT::GetLastObs(uint8* Buffer)
{
    while (bIsBusy) {}
    if (LastObservation != nullptr) {
        if (Modified) {
            TakeObs();
            Modified = false;
        }
        if (bEnvStep) {
            TakeObs();
        }
        bIsBusy = true;
        memcpy(Buffer, LastObservation, GetObservationSize());
        bIsBusy = false;
        return true;
    }
    return false;
}

const bool ADepthCameraSDT::TakeObs()
{
    bool ReadIsSuccessful;
    while (bIsBusy) {/*Waiting*/ }
    if (LevelManager->GetLevelMode() != 0) {
        while (LevelManager->IsBusy()) {
            UE_LOG(LogTemp, Error, TEXT("Level manager is busy..."));
        }
        LevelManager->SetLevelMode(0);
    }

    if (ActorsToHide.Num() != 0) {
        Camera->HiddenActors = ActorsToHide;
    }

    Camera->CaptureScene();
    LastObservationTimestamp = FDateTime::Now().ToString();
    TArray<FFloat16Color> FloatColorDepthData;
    Width = RenderTarget->SizeX;
    Height = RenderTarget->SizeY;
    //TArray<FColor> SurfData; //stores data loaded from renderTarget
    ReadIsSuccessful = RenderTarget->GameThread_GetRenderTargetResource()->ReadFloat16Pixels(FloatColorDepthData);
    uint32 Index = 0;
    uint8* FloatNumber = new uint8[sizeof(float)];
    bIsBusy = true;
    for (auto Pixel = FloatColorDepthData.CreateIterator(); Pixel; ++Pixel)
    {
        float f = Pixel->R;
        //UE_LOG(LogTemp, Warning, TEXT("Text, %f"), f);
        //char* s = (char*)&f;
        memcpy(FloatNumber, &f, sizeof(f));
        LastObservation[Index] = FloatNumber[0];
        Index++;
        LastObservation[Index] = FloatNumber[1];
        Index++;
        LastObservation[Index] = FloatNumber[2];
        Index++;
        LastObservation[Index] = FloatNumber[3];
        Index++;
    }

    bIsBusy = false;
    return ReadIsSuccessful;
}

const void ADepthCameraSDT::SetTickMode(bool Value)
{
    enableIndependentTick = Value;
    PrimaryActorTick.bCanEverTick = enableIndependentTick;
}
