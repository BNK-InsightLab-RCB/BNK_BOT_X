package org.bnkbotxapi.bnkbotxapi.security.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.bnkbotxapi.bnkbotxapi.account.domain.AccountEntity;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;

@Component
public class JWTUtil {

    @Value("${bnk.jwt.secret}")
    private String secret;

    @Value("${bnk.jwt.access-minutes}")
    private long accessMinutes;

    @Value("${bnk.jwt.refresh-minutes}")
    private long refreshMinutes;

    public String makeAccessToken(AccountEntity account) {
        return makeToken(account, accessMinutes);
    }

    public String makeRefreshToken(AccountEntity account) {
        return makeToken(account, refreshMinutes);
    }

    public Claims validate(String token) {
        return Jwts.parser()
                .verifyWith(signingKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private String makeToken(AccountEntity account, long minutes) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(account.getLoginId())
                .claim("accountId", account.getAccountId())
                .claim("name", account.getName())
                .claim("role", account.getRole().name())
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plus(minutes, ChronoUnit.MINUTES)))
                .signWith(signingKey(), Jwts.SIG.HS256)
                .compact();
    }

    private SecretKey signingKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
}
