from fastapi import APIRouter, HTTPException
from models import DiagnosisRequest, DiagnosisResponse
from memory import get_session, add_message, create_session
from agents.orchestrator import run_diagnosis_pipeline

router = APIRouter()


@router.post("/diagnosis", response_model=DiagnosisResponse)
async def run_diagnosis(body: DiagnosisRequest):
    sess = get_session(body.session_id)
    if not sess:
        # Auto-create session if not exists
        create_session(body.patient_info)

    try:
        result = await run_diagnosis_pipeline(
            session_id=body.session_id,
            symptoms=body.symptoms,
            duration=body.duration or "",
            severity=body.severity_level or "",
            patient_info=body.patient_info,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis pipeline failed: {str(e)}")

    return DiagnosisResponse(
        session_id=body.session_id,
        triage=result["triage"],
        symptom_analysis=result["symptom_analysis"],
        diagnosis=result["diagnosis"],
        treatment=result["treatment"],
        references=result["references"],
    )
